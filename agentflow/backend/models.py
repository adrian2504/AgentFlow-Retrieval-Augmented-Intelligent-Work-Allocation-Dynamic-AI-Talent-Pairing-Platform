from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum

class Status(str, Enum):
    queued = "queued"
    in_progress = "in_progress"
    done = "done"

class Task(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    project_id: str = Field(index=True)
    title: str
    routed_to: str
    owner: Optional[str] = None
    status: Status = Status.queued
    result: Optional[str] = None
    why: Optional[str] = None   # <— new field to capture the "why"
