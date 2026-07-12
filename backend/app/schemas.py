from __future__ import annotations

from pydantic import BaseModel


class FarmSummary(BaseModel):
    name: str
    city: str
    state: str
    planting_zone: str


class ForecastSummary(BaseModel):
    date: str
    summary: str
    thunderstorm_risk: bool
    high_wind_mph: int | None
    heat_index_f: int | None


class TodayTask(BaseModel):
    id: str
    title: str
    due_date: str
    severity: str
    reason: str
    steps: list[str]
    source_rule: str | None


class WeekDayPlan(BaseModel):
    date: str
    task_count: int
    urgent_count: int
    watch_count: int
    top_task: str | None


class TodayResponse(BaseModel):
    farm: FarmSummary
    today: str
    forecast: ForecastSummary
    tasks: list[TodayTask]
    week: list[WeekDayPlan]


class MagicLinkRequest(BaseModel):
    email: str


class MagicLinkResponse(BaseModel):
    status: str
    dev_login_token: str | None = None


class VerifyRequest(BaseModel):
    token: str


class SessionResponse(BaseModel):
    session_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str


class FarmCreate(BaseModel):
    name: str
    city: str
    state: str
    planting_zone: str
    crops: list[str] = []


class FarmResponse(BaseModel):
    id: int
    name: str
    city: str
    state: str
    planting_zone: str
    crops: list[str]
