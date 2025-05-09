#!/usr/bin/env python3
from dotenv import load_dotenv
import os, sys, json
from openai import OpenAI

# Load .env from CWD
load_dotenv()

api_key  = os.getenv("RUNPOD_KEY")
base_url = os.getenv("RUNPOD_URL")

print("🔑 RUNPOD_KEY:", api_key)
print("🌐 RUNPOD_URL:", base_url)
if not api_key or not base_url:
    print("❌ Please set RUNPOD_KEY and RUNPOD_URL (including /openai/v1) in your .env", file=sys.stderr)
    sys.exit(1)

print("→ POSTing to:", f"{base_url}/chat/completions")

client = OpenAI(api_key=api_key, base_url=base_url)

resp = client.chat.completions.create(
    model=os.getenv("MODEL_NAME"),
    messages=[
        {
            "role": "system",
            "content": (
                "You are AgentFlow’s Task Analyzer. "
                "Given the SPEC below, break it into a JSON array of atomic tasks. "
                "Each task must have {id, title}.  "
                "Respond *only* with the JSON array—no extra text or Markdown."
            )
        },
        {
            "role": "user",
            "content": (
                "SPEC:\n"
                "Design an intelligent system that analyzes project requirements "
                "and automatically determines which tasks should be handled by AI agents "
                "versus human talent. It should implement a RAG pipeline, an adaptive router, "
                "and smooth AI↔human handoffs."
            )
        }
    ],
)

out = resp.to_dict()
with open("runpod_response.json", "w") as f:
    json.dump(out, f, indent=2)

print("✅ Saved RunPod output to runpod_response.json")
