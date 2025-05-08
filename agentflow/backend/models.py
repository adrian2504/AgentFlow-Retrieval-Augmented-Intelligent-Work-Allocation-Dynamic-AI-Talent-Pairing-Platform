from typing import Literal, Optional
from pydantic import BaseModel

class Task(BaseModel):
    id: str
    project_id: str
    title: str
    status: Literal["queued", "in_progress", "done"] = "queued"
    routed_to: Literal["ai", "human"]
    owner: Optional[str] = None
    result: Optional[str] = None
