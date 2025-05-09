"""
Thin wrapper for your **chat‑only** RunPod endpoint (OpenAI‑compatible).
Embeddings are handled by a separate endpoint, so they are **not** included
here.
"""
import json
import os
import requests
from functools import lru_cache
from types import SimpleNamespace
from typing import Any, Dict, List

# ── Chat endpoint env ───────────────────────────────────────────────────────
API_KEY  = os.getenv("RUNPOD_CHAT_KEY") or os.getenv("RUNPOD_KEY")
BASE_URL = os.getenv("RUNPOD_CHAT_URL") or os.getenv("RUNPOD_URL")

CHAT_URL = BASE_URL.rstrip("/") + "/openai/v1/chat/completions"
HEADERS  = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type":  "application/json",
}

# ── Chat completions client ────────────────────────────────────────────────
class _ChatCompletions:
    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 512,
        **_: Any,
    ) -> SimpleNamespace:
        payload = {
            "model":       model,
            "messages":    messages,
            "temperature": temperature,
            "max_tokens":  max_tokens,
        }
        resp = requests.post(CHAT_URL, headers=HEADERS, json=payload, timeout=900)
        resp.raise_for_status()
        data    = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )

# ── Factory ────────────────────────────────────────────────────────────────
class RunPodClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=_ChatCompletions())

@lru_cache
def get_client() -> RunPodClient:
    return RunPodClient()
