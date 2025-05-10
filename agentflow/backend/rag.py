# rag.py

from __future__ import annotations

from pathlib import Path
import json
import logging
import os
from typing import List, Union
import requests

from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings

# ── Data dir ────────────────────────────────────────────────────────────────
DATA_DIR = Path("data/projects")
DATA_DIR.mkdir(parents=True, exist_ok=True)
log = logging.getLogger("rag")

# ── Embeddings endpoint env ────────────────────────────────────────────────
RUNPOD_EMBED_URL = os.getenv("RUNPOD_EMBED_URL")  # https://api.runpod.ai/v2/<embed-id>
RUNPOD_EMBED_KEY = os.getenv("RUNPOD_EMBED_KEY")
EMBED_MODEL      = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

if not (RUNPOD_EMBED_URL and RUNPOD_EMBED_KEY):
    raise RuntimeError("RUNPOD_EMBED_URL and RUNPOD_EMBED_KEY must be set for embeddings.")

# ── Embeddings client ───────────────────────────────────────────────────────
class RunPodEmbeddings(Embeddings):
    """LangChain-compatible: hits <base>/openai/v1/embeddings with its own key."""
    def __init__(self, base_url: str, api_key: str, model: str):
        self.url     = base_url.rstrip("/") + "/openai/v1/embeddings"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        }
        self.model = model

    def _call(self, inputs: List[str]) -> List[List[float]]:
        resp = requests.post(
            self.url,
            headers=self.headers,
            json={"model": self.model, "input": inputs},
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if not data:
            log.error("Embeddings endpoint returned empty for inputs: %s", inputs)
            raise RuntimeError("Empty embeddings")
        return [item["embedding"] for item in data]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._call(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._call([text])[0]

_EMB = RunPodEmbeddings(RUNPOD_EMBED_URL, RUNPOD_EMBED_KEY, EMBED_MODEL)
log.info("🟢 Using dedicated embeddings endpoint (%s)", EMBED_MODEL)

# ── Helper functions ───────────────────────────────────────────────────────
def save_raw(project_id: str, raw: Union[dict, list]) -> Path:
    fp = DATA_DIR / f"{project_id}.json"
    fp.write_text(json.dumps(raw, indent=2))
    return fp


def build_index(project_id: str, raw: Union[dict, list]) -> None:
    items = raw if isinstance(raw, list) else raw.get("tasks", [])
    if not items:
        log.warning("No tasks to embed for %s", project_id)
        return
    docs = [Document(page_content=json.dumps(it), metadata={}) for it in items]
    FAISS.from_documents(docs, _EMB).save_local(str(DATA_DIR / f"{project_id}.faiss"))
    log.info("✅ FAISS index built for %s (%d docs)", project_id, len(docs))


def _load(project_id: str):
    fp = DATA_DIR / f"{project_id}.faiss"
    if not fp.exists():
        return None
    # We created the file ourselves, so deserialization is safe
    return FAISS.load_local(
        str(fp),
        _EMB,
        allow_dangerous_deserialization=True,   # <- new flag
    )


def query(project_id: str, text: str, k: int = 3) -> List[dict]:
    idx = _load(project_id)
    if not idx:
        return []
    return [json.loads(d.page_content) for d in idx.similarity_search(text, k=k)]


def retrieve(text: str, project_id: str, k: int = 4) -> str:
    idx = _load(project_id)
    if not idx:
        return ""
    docs = idx.similarity_search(text, k=k)
    return "\n".join(d.page_content for d in docs)
