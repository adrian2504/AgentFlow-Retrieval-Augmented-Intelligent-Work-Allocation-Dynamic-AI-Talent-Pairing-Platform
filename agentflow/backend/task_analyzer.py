import os, json, uuid
from .openai_client import get_client
from .models import Task

client = get_client()
MODEL = os.getenv("MODEL_NAME")

PROMPT = """Break the following project brief into the smallest independent tasks.
Return ONLY valid JSON: [{"title": "...", "routed_to": "ai"|"human"}, ...].

BRIEF:
\"\"\"{spec}\"\"\"
"""

async def analyze(project_id: str, spec: str) -> list[Task]:
    resp = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"user","content":PROMPT.format(spec=spec)}],
        max_tokens=512,
        temperature=0.2,
    )
    
    items = json.loads(resp.choices[0].message.content)
    return [
        Task(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title=item["title"],
            routed_to=item["routed_to"],
            owner="LLM‑Llama‑3" if item["routed_to"] == "ai" else None,
        )
        for item in items
    ]
