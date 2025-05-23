from enum import Enum

from pydantic import BaseModel, Field

class Status(str, Enum):
    NOT_STARTED = "not started"
    IN_PROGRESS = "in progress"
    COMPLETED = "completed"


class Task(BaseModel):
    id: str | None = None
    task: str
    description: str | None = None
    duration_minutes: int | None = None
    resources: list[str] = []
    status: Status = Status.NOT_STARTED
    topic_id: str | None = None

class Topic(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    duration_days: int | None = None
    resources: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)

class Roadmap(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    total_duration_weeks: int | None = None
    topics: list[Topic] = Field(default_factory=list)
