# backend/orchestrator.py
import os, asyncio
from typing import Callable, Awaitable, List

from .openai_client import get_client
from .models import Task
from .rag import retrieve

client = get_client()
MODEL = os.getenv("MODEL_NAME")


# ─── task runners ──────────────────────────────────────────────────────────
async def run_ai(task: Task) -> str:
    ctx = retrieve(task.title, task.project_id)
    prompt = f"{ctx}\n\n### TASK\n{task.title}"
    rsp = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.2,
    )
    return rsp.choices[0].message.content


async def simulate_human(task: Task) -> str:
    await asyncio.sleep(20)
    return f"✅ {task.owner or 'Human'} finished: {task.title}"


# ─── background worker ─────────────────────────────────────────────────────
async def worker(
    queue: "asyncio.Queue[Task]",
    broadcast: Callable[[List[Task]], Awaitable[None]],
) -> None:
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
