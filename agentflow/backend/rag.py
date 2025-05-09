"""
RAG helper that picks between direct RunPod `/run` embeddings or
OpenAI-compatible embeddings via get_client.
"""
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

from .openai_client import get_client

# ── Data directory ──────────────────────────────────────────────────────────
DATA_DIR = Path("data/projects")
DATA_DIR.mkdir(parents=True, exist_ok=True)
log = logging.getLogger("rag")

# ── Environment ─────────────────────────────────────────────────────────────
RUNPOD_EMBED_URL = os.getenv("RUNPOD_EMBED_URL")
RUNPOD_EMBED_KEY = os.getenv("RUNPOD_EMBED_KEY")
EMBED_MODEL      = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# ── Embeddings selection ────────────────────────────────────────────────────
if RUNPOD_EMBED_URL and RUNPOD_EMBED_KEY:
    class RunPodDirectEmbeddings(Embeddings):
        """
        LangChain-compatible embeddings class calling a non-OpenAI `/run` endpoint.
        """
        def __init__(self, url: str, api_key: str, model: str) -> None:
            self.url     = url.rstrip("/") + "/run"
            self.headers = {"Authorization": f"Bearer {api_key}"}
            self.model   = model

        def _embed(self, texts: List[str]) -> List[List[float]]:
            payload = {"input": texts, "model": self.model}
            r = requests.post(self.url, headers=self.headers, json=payload, timeout=90)
            r.raise_for_status()
            out = r.json()
            vectors = out.get("output", out) if isinstance(out, dict) else out
            if not isinstance(vectors, list):
                raise ValueError(f"Unexpected embedding response: {out}")
            return vectors

        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            return self._embed(texts)

        def embed_query(self, text: str) -> List[float]:
            return self._embed([text])[0]

    _EMB = RunPodDirectEmbeddings(RUNPOD_EMBED_URL, RUNPOD_EMBED_KEY, EMBED_MODEL)
    log.info("🟢 Using direct RunPod embeddings (%s)", EMBED_MODEL)

else:
    client = get_client()
    class OpenAIEmbeddingsAdapter(Embeddings):
        """
        LangChain-compatible embeddings class using RunPod's OpenAI-compatible API.
        """
        def __init__(self, model: str) -> None:
            self.model = model

        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            resp = client.embeddings.create(model=self.model, input=texts)
            if not getattr(resp, "data", None):
                log.error("Embeddings API returned empty data for texts: %s", texts)
                raise RuntimeError("No embeddings returned from embeddings API")
            return [item["embedding"] for item in resp.data]

        def embed_query(self, text: str) -> List[float]:
            resp = client.embeddings.create(model=self.model, input=[text])
            if not getattr(resp, "data", None):
                log.error("Embeddings API returned empty data for query: %s", text)
                raise RuntimeError("No embeddings returned from embeddings API")
            return resp.data[0]["embedding"]

    _EMB = OpenAIEmbeddingsAdapter(EMBED_MODEL)
    log.info("🟢 Using OpenAI-compatible embeddings (%s)", EMBED_MODEL)

# ── Helpers ─────────────────────────────────────────────────────────────────
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
    return FAISS.load_local(str(fp), _EMB) if fp.exists() else None

def query(project_id: str, text: str, k: int = 3) -> List[dict]:
    idx = _load(project_id)
    if not idx:
        return []
    docs = idx.similarity_search(text, k=k)
    return [json.loads(d.page_content) for d in docs]

def retrieve(text: str, project_id: str, k: int = 4) -> str:
    idx = _load(project_id)
    if not idx:
        return ""
    docs = idx.similarity_search(text, k=k)
    return "\n".join(d.page_content for d in docs)
