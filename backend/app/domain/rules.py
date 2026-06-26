from __future__ import annotations

from datetime import date

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
}


ZONE_8B_SEASONAL_TASKS = {
    1: ["Review seed inventory and greenhouse start plan."],
    2: ["Start warm-season seedlings under protection."],
    3: ["Prepare beds and harden off early transplants."],
    4: ["Transplant warm-season crops when frost risk passes."],
    5: ["Scout tomatoes and cucurbits twice weekly."],
    6: ["Scout for tomato hornworms and early blight pressure."],
    7: ["Monitor heat stress and keep irrigation consistent."],
    8: ["Plan fall crop starts and watch pest pressure."],
    9: ["Start fall greens and prepare row cover."],
    10: ["Protect late crops from early cold snaps."],
    11: ["Clean up crop residue and update next season notes."],
    12: ["Review records and repair tools before spring planning."],
}


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

    return tasks
