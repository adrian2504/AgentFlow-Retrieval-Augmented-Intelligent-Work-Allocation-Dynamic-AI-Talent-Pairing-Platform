import os
from functools import lru_cache
from openai import OpenAI

@lru_cache
def get_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("RUNPOD_API_KEY"),
        base_url=os.getenv("RUNPOD_BASE_URL"),
    )
