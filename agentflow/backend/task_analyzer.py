# backend/task_analyzer.py

from __future__ import annotations
import asyncio
import json
import logging
import os
import re
import uuid
from typing import Any, List

from .models import Task
from .openai_client import get_client

log = logging.getLogger(__name__)

MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-8B-Instruct")

def _make_prompt(spec: str) -> str:
    """
    Build a prompt that embeds the raw spec literally, without
    confusing Python's formatter for {placeholders}.
    Any literal braces in the example JSON must be doubled.
    """
    return f"""
You are the orchestration lead on a hybrid‑talent delivery team.
Given a *single* project brief, output **ONLY** a top‑level JSON array of objects
describing the atomic work units and who should own them.

Example of exactly what to output (no extra keys, no markdown):

[{{  
  "title": "Draft architecture diagram",  
  "routed_to": "ai",  
  "why": "Image models can generate diagrams quickly"  
}}, {{  
  "title": "Validate architecture with security team",  
  "routed_to": "human",  
  "why": "Requires domain-specific governance knowledge"  
}}]

Rules
1. Break the project into the **smallest independent tasks** that can run in parallel.
2. For each task choose:
   • "ai"    when an LLM/automation can complete it to spec  
   • "human" when human expertise or approval is required
3. Add a short "why" (5–15 words) explaining your choice if you can.
4. The entire reply **MUST** be exactly a JSON array. No wrapper objects. No prose.

Project brief (do not include in your output):
\"\"\"{spec}\"\"\"
""".strip()

_client = get_client()

# ── helpers ─────────────────────────────────────────────────────────────────

fence_re = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.S)

def _strip_fences(txt: str) -> str:
    m = fence_re.search(txt)
    return m.group(1).strip() if m else txt.strip()

def _sanitize_field(val: Any) -> str:
    return str(val).strip(' "\'')

def _parse_tasks(raw: Any) -> List[dict]:
    """
    Accept:
      - list of dicts
      - { tasks: [ ... ] }
      - single dict
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        if "tasks" in raw and isinstance(raw["tasks"], list):
            return raw["tasks"]
        if {"title", "routed_to"} <= raw.keys():
            return [raw]
    return []

# ── main API ────────────────────────────────────────────────────────────────

async def analyze(project_id: str, spec: str) -> tuple[list[dict], List[Task]]:
    # 1. build prompt & call LLM
    prompt = _make_prompt(spec)
    rsp = await asyncio.to_thread(
        _client.chat.completions.create,
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=512,
    )
    raw_text = _strip_fences(rsp.choices[0].message.content)

    # debug: show exactly what we got
    log.debug("⚡ RAW LLM reply: %s", raw_text.replace('\n', ' ⏎ '))
    log.debug("⚡ JSON payload candidate: %r", raw_text)

    # 2. parse JSON
    try:
        raw_json = json.loads(raw_text)
    except json.JSONDecodeError as err:
        log.error("❌ Failed to JSON‑parse LLM reply:\n%s", raw_text)
        raise RuntimeError(f"LLM returned invalid JSON:\n{raw_text}") from err

    log.debug("⚡ Parsed JSON object: %s", raw_json)

    # 3. extract task dicts
    dicts = _parse_tasks(raw_json)
    log.debug("⚡ _parse_tasks yielded %d items: %s", len(dicts), dicts)

    tasks: List[Task] = []
    for d in dicts:
        if not isinstance(d, dict):
            continue
        title = _sanitize_field(d.get("title", ""))
        routed = _sanitize_field(d.get("routed_to", "")).lower()
        why    = _sanitize_field(d.get("why", "")) or None

        if not title or routed not in {"ai", "human"}:
            log.warning("Skipping malformed item: %s", d)
            continue

        tasks.append(Task(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title=title,
            routed_to=routed,
            why=why,
            owner="LLM-Llama-3" if routed == "ai" else None,
        ))

    if not tasks:
        raise RuntimeError("No valid tasks found in LLM output")

    return dicts, tasks
