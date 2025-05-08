from __future__ import annotations

import json
import os
import uuid
import logging
from typing import List

from fastapi import HTTPException, status

from .models import Task
from .openai_client import get_client

log = logging.getLogger(__name__)

MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama-3")
client = get_client()

# --------------------------------------------------------------------------- #
# Prompt template                                                             #
# --------------------------------------------------------------------------- #
PROMPT = """
You are a senior project manager. Split the project brief into the SMALLEST
independent work items.

Return ONLY valid JSON in **this exact shape**:

[
  {{"title": "Write project README", "routed_to": "ai"}},
  {{"title": "Implement FastAPI auth", "routed_to": "human"}}
]

• title: short action phrase
• routed_to: "ai" or "human"
DO NOT wrap the JSON in triple back‑ticks.
Project brief:
\"\"\"{spec}\"\"\"
"""


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def _sanitize(item: dict) -> dict[str, str]:
    """Strip stray quotes/spaces and lowercase the `routed_to` value."""
    if not isinstance(item, dict):
        return {}
    return {
        k.strip(' "\''): str(v).strip(' "\'').lower() for k, v in item.items()
    }


def _make_task(project_id: str, d: dict) -> Task:
    """Convert a clean dict to our Task dataclass."""
    return Task(
        id=str(uuid.uuid4()),
        project_id=project_id,
        title=d["title"],
        routed_to=d["routed_to"],
        owner="LLM‑Llama‑3" if d["routed_to"] == "ai" else None,
    )


# --------------------------------------------------------------------------- #
# Public entry‑point                                                          #
# --------------------------------------------------------------------------- #
async def analyze(project_id: str, spec: str) -> List[Task]:
    """
    Call the LLM and turn its JSON reply into a list[Task].

    Raises HTTPException(422) if the model can't give reasonable output.
    """
    log.info("Analyzing brief for project %s …", project_id)

    rsp = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": PROMPT.format(spec=spec)}],
        temperature=0.2,
        max_tokens=512,
    )

    raw = rsp.choices[0].message.content
    log.debug("LLM raw reply: %s", raw)

    # 1) Parse JSON safely
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.error("Bad JSON from LLM: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="LLM returned invalid JSON",
        ) from exc

    # 2) Sanitize + validate each item
    cleaned = []
    for item in data:
        item = _sanitize(item)
        if {"title", "routed_to"} <= item.keys() and item["routed_to"] in {"ai", "human"}:
            cleaned.append(item)
        else:
            log.warning("Skipping malformed task item: %s", item)

    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid tasks extracted from LLM output",
        )

    # 3) Build Task objects
    tasks = [_make_task(project_id, d) for d in cleaned]
    log.info("Analyzer produced %d tasks for project %s", len(tasks), project_id)
    return tasks