from enum import Enum
from pydantic import BaseModel, Field


class Status(str, Enum):
    status = ["not started", "in progress", "completed"]


class Task(BaseModel):
    id: str | None = None
    task: str
    description: str | None = None
    duration_minutes: int | None = None
    resources: list[str] = []
    prerequisites: list[str] = []
    status: Status = Status.status[0]


class Topic(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    duration_days: int | None = None
    resources: list[str] = []
    tasks: list[Task] = Field(default_factory=list)
