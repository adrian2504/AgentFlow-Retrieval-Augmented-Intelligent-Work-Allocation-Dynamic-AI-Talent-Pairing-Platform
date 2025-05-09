#!/usr/bin/env python3
import json
from pathlib import Path
from pydantic import BaseModel

class Task(BaseModel):
    id: str
    title: str

# 1) Load RunPod’s raw JSON
raw = json.loads(Path("runpod_response.json").read_text())
content = raw["choices"][0]["message"]["content"]

# 2) Parse the assistant’s content as JSON
tasks_list = json.loads(content)

# 3) Validate and print
tasks = [Task(**t) for t in tasks_list]
print("Parsed tasks:")
for t in tasks:
    print(f"- {t.id}: {t.title}")
