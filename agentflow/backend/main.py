import uuid, json, asyncio
from fastapi import FastAPI, WebSocket, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.models import Task
from .task_analyzer import analyze
from .router import route
from .orchestrator import worker

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

queue: asyncio.Queue[Task] = asyncio.Queue()
clients: set[WebSocket] = set()

async def broadcast(task: Task):
    data = task.model_dump_json()
    for ws in list(clients):
        await ws.send_text(data)

@app.websocket("/ws/tasks")
async def ws_tasks(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        pass
    finally:
        clients.remove(ws)

@app.post("/projects")
async def new_project(file: UploadFile):
    spec = (await file.read()).decode()
    project_id = str(uuid.uuid4())
    tasks = [route(t) for t in await analyze(project_id, spec)]
    for t in tasks:
        await queue.put(t)
        await broadcast(t)
    return {"project_id": project_id, "tasks": [t.id for t in tasks]}

@app.on_event("startup")
async def _start():
    asyncio.create_task(worker(queue, broadcast))
