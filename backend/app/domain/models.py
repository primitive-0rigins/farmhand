from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class TaskSeverity(StrEnum):
    INFO = "info"
    WATCH = "watch"
    URGENT = "urgent"


@dataclass(frozen=True)
class FarmAsset:
    name: str
    kind: str


@dataclass(frozen=True)
class FarmProfile:
    name: str
    city: str
    state: str
    planting_zone: str
    crops: list[str] = field(default_factory=list)
    assets: list[FarmAsset] = field(default_factory=list)

    def has_asset_kind(self, kind: str) -> bool:
        return any(asset.kind == kind for asset in self.assets)


@dataclass(frozen=True)
class WeatherForecast:
    forecast_date: date
    thunderstorm_risk: bool = False
    high_wind_mph: int | None = None
    frost_risk: bool = False
    heat_index_f: int | None = None
    heavy_rain_inches: float | None = None


@dataclass(frozen=True)
class Playbook:
    trigger: str
    title: str
    steps: list[str]


@dataclass(frozen=True)
class GeneratedTask:
    title: str
    due_date: date
    severity: TaskSeverity
    reason: str
    steps: list[str] = field(default_factory=list)
    source_rule: str | None = None
