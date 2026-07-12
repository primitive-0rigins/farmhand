from __future__ import annotations

import re
from datetime import date, timedelta

from app.domain.models import FarmProfile, GeneratedTask, Playbook, TaskSeverity, WeatherForecast


DEFAULT_PLAYBOOKS = {
    "bad_weather": Playbook(
        trigger="bad_weather",
        title="Bad weather prep",
        steps=[
            "Secure greenhouse doors, vents, and sidewalls.",
            "Move loose trays, buckets, and tools under cover.",
        ],
    ),
    "frost": Playbook(
        trigger="frost",
        title="Frost prep",
        steps=[
            "Stage row cover before sunset.",
            "Check tender crops and greenhouse heat backup.",
        ],
    ),
    "heat_irrigation": Playbook(
        trigger="heat_irrigation",
        title="Check irrigation before heat builds",
        steps=[
            "Walk main lines and look for leaks or clogged emitters.",
            "Water early enough that leaves dry before evening.",
        ],
    ),
}


ZONE_8B_SEASONAL_TASKS = {
    1: ["Review seed inventory and plan the growing season."],
    2: ["Service tools and turn compost before the season ramps up."],
    3: ["Prepare beds and harden off early transplants."],
    4: ["Mulch beds and set up trellises as the season warms."],
    5: ["Stay ahead of weeds and keep beds mulched."],
    6: ["Keep beds mulched and watch soil moisture as heat builds."],
    7: ["Monitor heat stress and keep irrigation consistent."],
    8: ["Plan fall crop starts and watch pest pressure."],
    9: ["Start fall greens and prepare row cover."],
    10: ["Protect late crops from early cold snaps."],
    11: ["Clean up crop residue and update next season notes."],
    12: ["Review records and repair tools before spring planning."],
}


WARM_SEASON_CROPS = frozenset({"tomato", "pepper"})


# Approximate USDA hardiness-zone frost anchors: (month of average last spring
# frost, month of average first fall frost). Coarse and month-granular on
# purpose. Only temperate zones 3-8 are modeled, where a spring-transplant /
# summer-harvest pattern holds. Warmer zones (9+) invert this into a winter
# growing season and are left to a future model rather than given confidently
# wrong advice.
ZONE_FROST = {
    3: (5, 9),
    4: (5, 9),
    5: (5, 10),
    6: (4, 10),
    7: (4, 11),
    8: (4, 11),
}


SEVERITY_ORDER = {
    TaskSeverity.URGENT: 0,
    TaskSeverity.WATCH: 1,
    TaskSeverity.INFO: 2,
}


def _task_sort_key(task: GeneratedTask) -> tuple[int, date, str]:
    return (SEVERITY_ORDER[task.severity], task.due_date, task.title)


def _warm_season_crops(farm: FarmProfile) -> list[str]:
    return sorted({crop.lower() for crop in farm.crops} & WARM_SEASON_CROPS)


def _zone_number(planting_zone: str) -> int | None:
    match = re.match(r"\s*(\d+)", planting_zone)
    return int(match.group(1)) if match else None


def generate_daily_tasks(
    farm: FarmProfile,
    forecast: WeatherForecast,
    today: date,
    playbooks: dict[str, Playbook] | None = None,
) -> list[GeneratedTask]:
    active_playbooks = {**DEFAULT_PLAYBOOKS, **(playbooks or {})}
    tasks: list[GeneratedTask] = []

    if farm.planting_zone.lower() == "8b":
        for title in ZONE_8B_SEASONAL_TASKS.get(today.month, []):
            tasks.append(
                GeneratedTask(
                    title=title,
                    due_date=today,
                    severity=TaskSeverity.INFO,
                    reason=f"{farm.city}, {farm.state} is configured as planting zone 8b.",
                    source_rule="zone_8b_monthly_calendar",
                )
            )

    if forecast.thunderstorm_risk or (forecast.high_wind_mph or 0) >= 30:
        playbook = active_playbooks["bad_weather"]
        steps = list(playbook.steps)
        if farm.has_asset_kind("tractor"):
            steps.append("Make sure tractor and implements are covered or parked safely.")
        tasks.append(
            GeneratedTask(
                title=playbook.title,
                due_date=forecast.forecast_date,
                severity=TaskSeverity.URGENT,
                reason="Thunderstorm or high wind risk is forecast for the farm.",
                steps=steps,
                source_rule="bad_weather_playbook",
            )
        )

    if forecast.frost_risk:
        playbook = active_playbooks["frost"]
        tasks.append(
            GeneratedTask(
                title=playbook.title,
                due_date=forecast.forecast_date,
                severity=TaskSeverity.URGENT,
                reason="Frost risk is forecast for tender crops.",
                steps=list(playbook.steps),
                source_rule="frost_playbook",
            )
        )

    if (forecast.heat_index_f or 0) >= 90 and farm.has_asset_kind("irrigation"):
        playbook = active_playbooks["heat_irrigation"]
        tasks.append(
            GeneratedTask(
                title=playbook.title,
                due_date=today,
                severity=TaskSeverity.WATCH,
                reason="Heat index is forecast above 90F and this farm has irrigation equipment.",
                steps=list(playbook.steps),
                source_rule="heat_irrigation_playbook",
            )
        )

    if "tomato" in {crop.lower() for crop in farm.crops} and (forecast.heavy_rain_inches or 0) >= 1:
        tasks.append(
            GeneratedTask(
                title="Scout tomatoes for leaf disease after wet weather.",
                due_date=forecast.forecast_date,
                severity=TaskSeverity.WATCH,
                reason="Recent or forecast rain above 1 inch raises tomato leaf disease pressure.",
                source_rule="tomato_wet_weather_disease_pressure",
            )
        )

    if "tomato" in {crop.lower() for crop in farm.crops} and today.month in {6, 7, 8}:
        tasks.append(
            GeneratedTask(
                title="Scout tomatoes for hornworms and leaf disease.",
                due_date=today,
                severity=TaskSeverity.WATCH,
                reason="Tomatoes are active on this farm and summer pest pressure is likely.",
                source_rule="tomato_summer_scouting",
            )
        )

    warm_season = _warm_season_crops(farm)
    zone_number = _zone_number(farm.planting_zone)
    frost = ZONE_FROST.get(zone_number) if zone_number is not None else None
    if warm_season and frost is not None:
        last_frost, first_frost = frost
        crop_list = ", ".join(warm_season)
        zone = farm.planting_zone
        if today.month == last_frost - 2:
            tasks.append(
                GeneratedTask(
                    title="Start warm-season seedlings under cover.",
                    due_date=today,
                    severity=TaskSeverity.INFO,
                    reason=f"Warm-season crops on this farm ({crop_list}) are usually started under cover ahead of zone {zone}'s last spring frost.",
                    source_rule="warm_season_greenhouse_start",
                )
            )
        if today.month == last_frost:
            tasks.append(
                GeneratedTask(
                    title="Transplant warm-season crops after the last frost.",
                    due_date=today,
                    severity=TaskSeverity.INFO,
                    reason=f"Zone {zone}'s last spring frost has typically passed, so warm-season crops on this farm ({crop_list}) can move outside.",
                    source_rule="warm_season_transplant",
                )
            )
        if last_frost + 2 <= today.month <= first_frost:
            tasks.append(
                GeneratedTask(
                    title="Harvest ripe warm-season crops.",
                    due_date=today,
                    severity=TaskSeverity.INFO,
                    reason=f"Warm-season crops on this farm ({crop_list}) are in their summer harvest window for zone {zone}, so pick ripe fruit regularly to keep plants producing.",
                    source_rule="warm_season_harvest_window",
                )
            )
        if today.month == last_frost - 1:
            tasks.append(
                GeneratedTask(
                    title="Watch the forecast for a late spring frost.",
                    due_date=today,
                    severity=TaskSeverity.WATCH,
                    reason=f"Zone {zone}'s last spring frost is about a month out, so start checking the nightly forecast and keep row cover ready before setting out tender crops.",
                    source_rule="frost_watch_spring",
                )
            )
        if today.month == first_frost - 1:
            tasks.append(
                GeneratedTask(
                    title="Watch the forecast for the first fall frost.",
                    due_date=today,
                    severity=TaskSeverity.WATCH,
                    reason=f"Zone {zone}'s first fall frost is about a month out, so start checking the nightly forecast and plan to protect or harvest tender crops.",
                    source_rule="frost_watch_fall",
                )
            )

    return sorted(tasks, key=_task_sort_key)


def generate_weekly_plan(
    farm: FarmProfile,
    forecasts: list[WeatherForecast],
    start_date: date,
    playbooks: dict[str, Playbook] | None = None,
) -> dict[date, list[GeneratedTask]]:
    forecast_by_date = {forecast.forecast_date: forecast for forecast in forecasts}
    plan: dict[date, list[GeneratedTask]] = {}

    for offset in range(7):
        plan_date = start_date + timedelta(days=offset)
        forecast = forecast_by_date.get(plan_date, WeatherForecast(forecast_date=plan_date))
        plan[plan_date] = generate_daily_tasks(
            farm=farm,
            forecast=forecast,
            today=plan_date,
            playbooks=playbooks,
        )

    return plan
