from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Protocol
from urllib.request import Request, urlopen

from app.domain.models import WeatherForecast

# The US National Weather Service API is free and public: no API key, no
# account, no farmer sign-in. It only asks clients to send a User-Agent that
# identifies the app and a contact address. That is set here by us, the
# developer -- never by the user.
NWS_USER_AGENT = "farmhand-demo (contact@example.com)"
NWS_API = "https://api.weather.gov"

# Temperatures at or below this (F) count as frost risk for tender crops.
FROST_THRESHOLD_F = 36


class WeatherProvider(Protocol):
    """Turns a location into typed daily forecasts the rules can read.

    The whole point of this seam: whatever fetches the weather (a government
    API, a commercial feed, even an AI that scrapes) must hand back structured
    WeatherForecast values, so the deterministic rules stay the source of truth.
    """

    def daily_forecasts(
        self, latitude: float, longitude: float
    ) -> list[WeatherForecast]:
        ...


class DemoWeatherProvider:
    """Canned, offline forecast so the demo and tests never touch the network."""

    def daily_forecasts(
        self, latitude: float, longitude: float
    ) -> list[WeatherForecast]:
        return [
            WeatherForecast(forecast_date=date(2026, 6, 26), heat_index_f=92),
            WeatherForecast(
                forecast_date=date(2026, 6, 27),
                thunderstorm_risk=True,
                high_wind_mph=34,
                heat_index_f=91,
            ),
            WeatherForecast(forecast_date=date(2026, 6, 28), heat_index_f=89),
            WeatherForecast(forecast_date=date(2026, 6, 29), heavy_rain_inches=1.1),
            WeatherForecast(forecast_date=date(2026, 6, 30), heat_index_f=93),
            WeatherForecast(forecast_date=date(2026, 7, 1), heat_index_f=95),
            WeatherForecast(forecast_date=date(2026, 7, 2), heat_index_f=88),
        ]


class NWSWeatherProvider:
    """US National Weather Service adapter. Free, public, no API key."""

    def daily_forecasts(
        self, latitude: float, longitude: float
    ) -> list[WeatherForecast]:
        points = self._get(f"{NWS_API}/points/{latitude},{longitude}")
        forecast = self._get(points["properties"]["forecast"])
        return forecasts_from_nws_periods(forecast["properties"]["periods"])

    def _get(self, url: str) -> dict:
        request = Request(
            url,
            headers={"User-Agent": NWS_USER_AGENT, "Accept": "application/geo+json"},
        )
        with urlopen(request, timeout=10) as response:
            return json.load(response)


def forecasts_from_nws_periods(periods: list[dict]) -> list[WeatherForecast]:
    """Fold NWS day/night periods into one WeatherForecast per calendar day.

    Honest mapping notes:
    - frost_risk: any period that day at or below FROST_THRESHOLD_F.
    - thunderstorm_risk: "thunder" anywhere in the short forecast.
    - high_wind_mph: the largest number in the wind-speed text.
    - heat_index_f: the day's high temperature, used as a heat proxy. The
      friendly forecast endpoint does not expose heat index directly.
    - heavy_rain_inches: left unset. This endpoint reports rain *chance*, not
      measured inches; real amounts come from the gridpoint precipitation
      series, which a later pass can add. Better to report nothing than to
      invent an inch count.
    """
    by_day: dict[date, list[dict]] = {}
    for period in periods:
        day = datetime.fromisoformat(period["startTime"]).date()
        by_day.setdefault(day, []).append(period)

    forecasts: list[WeatherForecast] = []
    for day in sorted(by_day):
        day_periods = by_day[day]
        temps = [
            p["temperature"] for p in day_periods if p.get("temperature") is not None
        ]
        highs = [
            p["temperature"]
            for p in day_periods
            if p.get("isDaytime") and p.get("temperature") is not None
        ]
        winds = [
            w
            for p in day_periods
            if (w := _max_wind_mph(p.get("windSpeed", ""))) > 0
        ]
        thunder = any(
            "thunder" in (p.get("shortForecast") or "").lower() for p in day_periods
        )
        forecasts.append(
            WeatherForecast(
                forecast_date=day,
                thunderstorm_risk=thunder,
                high_wind_mph=max(winds) if winds else None,
                frost_risk=any(t <= FROST_THRESHOLD_F for t in temps) if temps else False,
                heat_index_f=max(highs) if highs else None,
            )
        )
    return forecasts


def _max_wind_mph(wind_speed: str) -> int:
    numbers = [int(match) for match in re.findall(r"\d+", wind_speed)]
    return max(numbers) if numbers else 0
