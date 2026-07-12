from datetime import date

from app.domain.models import FarmAsset, FarmProfile, Playbook, TaskSeverity, WeatherForecast
from app.domain.rules import generate_daily_tasks, generate_weekly_plan


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


def test_tomato_disease_pressure_follows_heavy_rain() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato"],
    )
    forecast = WeatherForecast(
        forecast_date=date(2026, 6, 29),
        heavy_rain_inches=1.2,
    )

    tasks = generate_daily_tasks(farm, forecast, today=date(2026, 6, 28))

    disease_task = next(
        task for task in tasks if task.source_rule == "tomato_wet_weather_disease_pressure"
    )
    assert disease_task.severity == TaskSeverity.WATCH
    assert "disease pressure" in disease_task.reason
    assert disease_task.due_date == date(2026, 6, 29)


def test_tomato_disease_pressure_requires_tomato_crop() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["pepper"],
    )
    forecast = WeatherForecast(
        forecast_date=date(2026, 6, 29),
        heavy_rain_inches=1.2,
    )

    tasks = generate_daily_tasks(farm, forecast, today=date(2026, 6, 28))

    assert not any(
        task.source_rule == "tomato_wet_weather_disease_pressure" for task in tasks
    )


def test_generated_tasks_are_sorted_for_today_dashboard() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato"],
        assets=[
            FarmAsset(name="Main greenhouse", kind="greenhouse"),
            FarmAsset(name="Drip irrigation", kind="irrigation"),
        ],
    )
    forecast = WeatherForecast(
        forecast_date=date(2026, 6, 27),
        thunderstorm_risk=True,
        heat_index_f=94,
    )

    tasks = generate_daily_tasks(farm, forecast, today=date(2026, 6, 26))

    assert [task.severity for task in tasks] == [
        TaskSeverity.URGENT,
        TaskSeverity.WATCH,
        TaskSeverity.WATCH,
        TaskSeverity.INFO,
    ]
    assert tasks[0].source_rule == "bad_weather_playbook"


def test_weekly_plan_returns_seven_days_from_start_date() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
    )

    plan = generate_weekly_plan(
        farm=farm,
        forecasts=[],
        start_date=date(2026, 6, 26),
    )

    assert list(plan) == [
        date(2026, 6, 26),
        date(2026, 6, 27),
        date(2026, 6, 28),
        date(2026, 6, 29),
        date(2026, 6, 30),
        date(2026, 7, 1),
        date(2026, 7, 2),
    ]


def test_weekly_plan_applies_forecast_to_matching_day() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        assets=[FarmAsset(name="Main greenhouse", kind="greenhouse")],
    )
    forecast = WeatherForecast(
        forecast_date=date(2026, 6, 28),
        thunderstorm_risk=True,
        high_wind_mph=32,
    )

    plan = generate_weekly_plan(
        farm=farm,
        forecasts=[forecast],
        start_date=date(2026, 6, 26),
    )

    assert any(task.source_rule == "bad_weather_playbook" for task in plan[date(2026, 6, 28)])
    assert not any(task.source_rule == "bad_weather_playbook" for task in plan[date(2026, 6, 27)])
