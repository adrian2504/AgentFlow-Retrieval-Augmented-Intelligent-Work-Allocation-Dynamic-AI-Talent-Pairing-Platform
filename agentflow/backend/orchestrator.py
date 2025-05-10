# backend/orchestrator.py

from __future__ import annotations

import asyncio
import os
from typing import Callable, Awaitable, List

from .openai_client import get_client
from .models import Task
from .rag import retrieve

client = get_client()
MODEL  = os.getenv("MODEL_NAME") or "meta-llama/Meta-Llama-3-8B-Instruct"

# ── task runners ─────────────────────────────────────────────────────────────
async def run_ai(task: Task) -> str:
    """Embed context + call chat completions in a background thread."""
    ctx = retrieve(task.title, task.project_id)
    prompt = f"{ctx}\n\n### TASK\n{task.title}"

    # `client.chat.completions.create` is **blocking**; off‑load with to_thread
    rsp = await asyncio.to_thread(
        client.chat.completions.create,
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.2,
    )
    return rsp.choices[0].message.content.strip()


async def simulate_human(task: Task) -> str:
    await asyncio.sleep(20)
    return f"✅ {task.owner or 'Human'} finished: {task.title}"


# ── background worker loop ─────────────────────────────────────────────────--
async def worker(
    queue: "asyncio.Queue[Task]",
    broadcast: Callable[[List[Task]], Awaitable[None]],
) -> None:
    """Continuously pull tasks from the queue, run them, broadcast status."""
    while True:
        task: Task = await queue.get()

        task.status = "in_progress"
        await broadcast([task])

        task.result = await (
            run_ai(task) if task.routed_to == "ai" else simulate_human(task)
        )

        task.status = "done"
        await broadcast([task])

        queue.task_done()
