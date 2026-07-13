from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


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
    crops: list[str] = Field(default_factory=list)

    @field_validator("name", "city", "state", "planting_zone")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("crops")
    @classmethod
    def normalized_crops(cls, values: list[str]) -> list[str]:
        crops = [crop.strip().lower() for crop in values]
        if any(not crop for crop in crops):
            raise ValueError("crop names must not be blank")
        return list(dict.fromkeys(crops))


class FarmResponse(BaseModel):
    id: int
    name: str
    city: str
    state: str
    planting_zone: str
    crops: list[str]
    assets: list["FarmAssetResponse"]
    spaces: list["GrowingSpaceResponse"]


class FarmAssetCreate(BaseModel):
    name: str
    kind: str

    @field_validator("name")
    @classmethod
    def required_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("kind")
    @classmethod
    def normalized_kind(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("must not be blank")
        return value


class FarmAssetResponse(BaseModel):
    id: int
    name: str
    kind: str


class GrowingSpaceCreate(BaseModel):
    name: str
    kind: Literal["field", "greenhouse", "high_tunnel", "orchard", "pasture"]

    @field_validator("name")
    @classmethod
    def required_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class GrowingSpaceResponse(BaseModel):
    id: int
    name: str
    kind: str
