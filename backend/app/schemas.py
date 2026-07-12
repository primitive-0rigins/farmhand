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


class TodayResponse(BaseModel):
    farm: FarmSummary
    today: str
    forecast: ForecastSummary
    tasks: list[TodayTask]
