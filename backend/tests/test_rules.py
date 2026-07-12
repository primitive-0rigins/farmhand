from datetime import date

from app.domain.models import FarmAsset, FarmProfile, Playbook, TaskSeverity, WeatherForecast
from app.domain.rules import generate_daily_tasks


def test_zone_calendar_generates_monthly_task() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
    )
    forecast = WeatherForecast(forecast_date=date(2026, 6, 27))

    tasks = generate_daily_tasks(farm, forecast, today=date(2026, 6, 26))

    assert any(task.source_rule == "zone_8b_monthly_calendar" for task in tasks)


def test_bad_weather_uses_custom_playbook_and_assets() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        assets=[
            FarmAsset(name="Main greenhouse", kind="greenhouse"),
            FarmAsset(name="Kubota", kind="tractor"),
        ],
    )
    forecast = WeatherForecast(
        forecast_date=date(2026, 6, 27),
        thunderstorm_risk=True,
    )
    playbooks = {
        "bad_weather": Playbook(
            trigger="bad_weather",
            title="Storm prep",
            steps=["Latch sidewalls.", "Move seed trays off low benches."],
        )
    }

    tasks = generate_daily_tasks(
        farm,
        forecast,
        today=date(2026, 6, 26),
        playbooks=playbooks,
    )

    storm_task = next(task for task in tasks if task.source_rule == "bad_weather_playbook")
    assert storm_task.title == "Storm prep"
    assert storm_task.severity == TaskSeverity.URGENT
    assert "Move seed trays off low benches." in storm_task.steps
    assert any("tractor" in step for step in storm_task.steps)


def test_tomato_scouting_arrives_in_summer() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato"],
    )
    forecast = WeatherForecast(forecast_date=date(2026, 7, 1))

    tasks = generate_daily_tasks(farm, forecast, today=date(2026, 7, 1))

    assert any(task.source_rule == "tomato_summer_scouting" for task in tasks)


def test_heat_irrigation_rule_requires_heat_and_irrigation_asset() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        assets=[FarmAsset(name="Drip irrigation", kind="irrigation")],
    )
    forecast = WeatherForecast(
        forecast_date=date(2026, 7, 2),
        heat_index_f=94,
    )

    tasks = generate_daily_tasks(farm, forecast, today=date(2026, 7, 1))

    heat_task = next(task for task in tasks if task.source_rule == "heat_irrigation_playbook")
    assert heat_task.severity == TaskSeverity.WATCH
    assert "irrigation equipment" in heat_task.reason
    assert heat_task.due_date == date(2026, 7, 1)


def test_heat_irrigation_rule_does_not_fire_without_irrigation() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
    )
    forecast = WeatherForecast(
        forecast_date=date(2026, 7, 2),
        heat_index_f=94,
    )

    tasks = generate_daily_tasks(farm, forecast, today=date(2026, 7, 1))

    assert not any(task.source_rule == "heat_irrigation_playbook" for task in tasks)
