from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["OPEN", "SCHEDULED", "IN_PROGRESS", "DONE"]
Priority = Literal["P1", "P2", "P3"]


class WorkOrderIn(BaseModel):
    turbine_id: str
    priority: Priority
    planned_date: date
    crew: str = Field(min_length=2, max_length=80)
    notes: str = Field(default="", max_length=2000)


class WorkOrderPatch(BaseModel):
    status: Status | None = None
    planned_date: date | None = None
    priority: Priority | None = None
    crew: str | None = None


class GenieAsk(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    conversation_id: str | None = None


class GenieAnswer(BaseModel):
    conversation_id: str
    message_id: str
    status: str
    text: str
    sql: str | None = None
    columns: list[str] = []
    rows: list[list] = []
    row_count: int = 0
