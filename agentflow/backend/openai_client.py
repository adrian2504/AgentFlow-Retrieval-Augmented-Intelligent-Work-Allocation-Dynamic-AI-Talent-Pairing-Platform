import json
import os
import requests
from functools import lru_cache
from types import SimpleNamespace
from typing import Any, List, Dict, Union

# ── Environment & Endpoints ──────────────────────────────────────────────────
API_KEY    = os.getenv("RUNPOD_CHAT_KEY") or os.getenv("RUNPOD_KEY")
BASE_URL   = os.getenv("RUNPOD_CHAT_URL") or os.getenv("RUNPOD_URL")  # no trailing slash
CHAT_URL   = BASE_URL.rstrip("/") + "/openai/v1/chat/completions"
EMBED_URL  = BASE_URL.rstrip("/") + "/openai/v1/embeddings"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type":  "application/json",
}

# ── Helpers ─────────────────────────────────────────────────────────────────
def _to_str(obj: Any) -> str:
    """
    Ensure the object is returned as a string; JSON-serialize if not already.
    """
    return obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False)

# ── Chat Completions ────────────────────────────────────────────────────────
class _ChatCompletions:
    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 512,
        **_: Any,
    ) -> SimpleNamespace:
        """
        Send a chat completion request to the RunPod OpenAI-compatible API.
        Blocks until completion (up to HTTP timeout).
        """
        payload = {
            "model":       model,
            "messages":    messages,
            "temperature": temperature,
            "max_tokens":  max_tokens,
        }
        # Timeout set high to cover lengthy GPU runs (e.g., 15m)
        resp = requests.post(CHAT_URL, headers=HEADERS, json=payload, timeout=900)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"].strip()
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )

# ── Embeddings ─────────────────────────────────────────────────────────────
class _Embeddings:
    def create(
        self,
        model: str,
        input: Union[str, List[str]],
        **_: Any,
    ) -> SimpleNamespace:
        """
        Send an embeddings request to the RunPod OpenAI-compatible API.
        """
        payload = {
            "model": model,
            "input": input,
        }
        # Shorter timeout; embeddings are typically faster
        resp = requests.post(EMBED_URL, headers=HEADERS, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        # `data` contains a list of {embedding: [...], index: int}
        return SimpleNamespace(data=data.get("data", []))

# ── Client Factory ─────────────────────────────────────────────────────────
class RunPodClient:
    """
    Provides `.chat.completions.create(...)` and `.embeddings.create(...)`
    interfaces compatible with OpenAI's Python API.
    """
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=_ChatCompletions())
        self.embeddings = SimpleNamespace(create=_Embeddings().create)

@lru_cache
def get_client() -> RunPodClient:
    """
    Return a singleton RunPodClient for OpenAI-compatible calls.
    """
    return RunPodClient()
