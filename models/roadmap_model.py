from pydantic import BaseModel, Field

class Task(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    estimated_time: str | None = None

class Topic(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    estimated_time: str | None = None
    resources: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)

class Roadmap(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    total_estimated_time: str | None = None
    topics: list[Topic] = Field(default_factory=list)
