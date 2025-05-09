# backend/main.py

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import List

from fastapi import (
    FastAPI, UploadFile, BackgroundTasks,
    WebSocket, WebSocketDisconnect, HTTPException
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.websockets import WebSocketState

from .models import Task
from .task_analyzer import analyze
from .rag import save_raw, build_index, query
from .router import route
from .orchestrator import worker

log = logging.getLogger("agentflow")
logging.basicConfig(level=logging.DEBUG)

app = FastAPI(title="AgentFlow OSS", version="0.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --------------------------------------------------------------------------- #
# WebSocket manager                                                           #
# --------------------------------------------------------------------------- #
class ConnectionManager:
    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)

    async def broadcast(self, tasks: List[Task]) -> None:
        if not self.active:
            return

        payload = json.dumps(
            [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "routedTo": t.routed_to,
                    "owner": t.owner,
                    "result": t.result,
                }
                for t in tasks
            ]
        )

        dead: List[WebSocket] = []
        for ws in self.active:
            if ws.application_state != WebSocketState.CONNECTED:
                dead.append(ws)
                continue
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()

# --------------------------------------------------------------------------- #
# background worker bootstrap                                                 #
# --------------------------------------------------------------------------- #
queue: "asyncio.Queue[Task]" = asyncio.Queue()


@app.on_event("startup")
async def _boot_background_worker() -> None:
    asyncio.create_task(worker(queue, manager.broadcast))
    log.info("👷 Background worker started")


# --------------------------------------------------------------------------- #
# request / response models                                                   #
# --------------------------------------------------------------------------- #
class ProjectResponse(BaseModel):
    project_id: str
    tasks: List[Task]


# --------------------------------------------------------------------------- #
# routes                                                                      #
# --------------------------------------------------------------------------- #
@app.post("/projects", response_model=ProjectResponse, status_code=202)
async def start_project(file: UploadFile, bg: BackgroundTasks):
    if file.content_type not in {"text/plain", "text/markdown", "application/pdf"}:
        raise HTTPException(400, "Unsupported file type")

    project_id = str(uuid.uuid4())
    spec = (await file.read()).decode(errors="ignore")
    log.info("📄 New project %s", project_id)

    bg.add_task(_process_project, project_id, spec)
    return ProjectResponse(project_id=project_id, tasks=[])


async def _process_project(project_id: str, spec: str) -> None:
    """
    Long-running pipeline (analyze → save raw → build FAISS → enqueue tasks).
    Runs in a FastAPI BackgroundTask so the POST returns immediately.
    """
    try:
        raw, tasks = await analyze(project_id, spec)
        save_raw(project_id, raw)
        build_index(project_id, raw)

        # route + enqueue every task
        for t in tasks:
            route(t)
            await queue.put(t)

        await manager.broadcast(tasks)
        log.info("✅ Project %s processed (%d tasks)", project_id, len(tasks))
    except Exception as err:
        log.exception("Processing %s failed: %s", project_id, err)


@app.get("/projects/{project_id}/raw")
def get_raw(project_id: str):
    fp = Path("data/projects") / f"{project_id}.json"
    if not fp.exists():
        raise HTTPException(404, "Project not found")
    return json.loads(fp.read_text())


@app.get("/projects/{project_id}/query")
def rag_query(project_id: str, q: str):
    return {"matches": [json.loads(m) for m in query(project_id, q)]}


@app.websocket("/ws/tasks")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive ping
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


# global fallback
@app.exception_handler(Exception)
async def _err(_, exc):
    log.exception("Unhandled: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
