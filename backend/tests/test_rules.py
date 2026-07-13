from datetime import date

from app.domain.models import CropPlanting, FarmAsset, FarmProfile, Playbook, TaskSeverity, WeatherForecast
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


def test_configured_succession_reminder_uses_the_farms_interval() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        plantings=[CropPlanting(crop="lettuce", planted_on=date(2026, 4, 1), succession_interval_days=14)],
    )
    tasks = generate_daily_tasks(farm, WeatherForecast(forecast_date=date(2026, 4, 15)), today=date(2026, 4, 15))

    reminder = next(task for task in tasks if task.source_rule == "configured_succession_planting")
    assert "lettuce" in reminder.title
    assert "14-day" in reminder.reason


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


def test_greenhouse_start_reminder_arrives_in_late_winter() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato", "pepper"],
    )
    forecast = WeatherForecast(forecast_date=date(2026, 2, 15))

    tasks = generate_daily_tasks(farm, forecast, today=date(2026, 2, 15))

    start_task = next(
        task for task in tasks if task.source_rule == "warm_season_greenhouse_start"
    )
    assert start_task.severity == TaskSeverity.INFO
    assert "pepper, tomato" in start_task.reason


def test_transplant_reminder_arrives_after_frost_season() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato"],
    )
    forecast = WeatherForecast(forecast_date=date(2026, 4, 20))

    tasks = generate_daily_tasks(farm, forecast, today=date(2026, 4, 20))

    assert any(task.source_rule == "warm_season_transplant" for task in tasks)


def test_harvest_window_arrives_in_summer_for_warm_season_crops() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["pepper"],
    )
    forecast = WeatherForecast(forecast_date=date(2026, 7, 10))

    tasks = generate_daily_tasks(farm, forecast, today=date(2026, 7, 10))

    harvest_task = next(
        task for task in tasks if task.source_rule == "warm_season_harvest_window"
    )
    assert harvest_task.severity == TaskSeverity.INFO
    assert harvest_task.due_date == date(2026, 7, 10)


def test_crop_timing_rules_skip_farms_without_warm_season_crops() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["lettuce"],
    )

    for today in (date(2026, 2, 15), date(2026, 4, 20), date(2026, 7, 10)):
        forecast = WeatherForecast(forecast_date=today)
        tasks = generate_daily_tasks(farm, forecast, today=today)
        assert not any(
            task.source_rule
            in {
                "warm_season_greenhouse_start",
                "warm_season_transplant",
                "warm_season_harvest_window",
                "frost_watch_spring",
                "frost_watch_fall",
            }
            for task in tasks
        )


def test_zone_calendar_does_not_duplicate_crop_timing_tasks() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato", "pepper"],
    )

    for today in (date(2026, 2, 15), date(2026, 4, 15)):
        forecast = WeatherForecast(forecast_date=today)
        tasks = generate_daily_tasks(farm, forecast, today=today)
        timing_tasks = [
            task
            for task in tasks
            if "seedling" in task.title.lower() or "transplant" in task.title.lower()
        ]
        assert len(timing_tasks) == 1
        assert timing_tasks[0].source_rule.startswith("warm_season_")


def test_crop_timing_shifts_with_planting_zone() -> None:
    cold = FarmProfile(
        name="North Farm",
        city="Duluth",
        state="MN",
        planting_zone="3",
        crops=["tomato"],
    )

    april = generate_daily_tasks(
        cold, WeatherForecast(forecast_date=date(2026, 4, 20)), today=date(2026, 4, 20)
    )
    assert not any(task.source_rule == "warm_season_transplant" for task in april)

    may = generate_daily_tasks(
        cold, WeatherForecast(forecast_date=date(2026, 5, 20)), today=date(2026, 5, 20)
    )
    assert any(task.source_rule == "warm_season_transplant" for task in may)


def test_crop_timing_quiet_for_unmodeled_zone() -> None:
    farm = FarmProfile(
        name="Gulf Farm",
        city="Miami",
        state="FL",
        planting_zone="10b",
        crops=["tomato", "pepper"],
    )

    for today in (date(2026, 2, 15), date(2026, 4, 15), date(2026, 7, 15)):
        forecast = WeatherForecast(forecast_date=today)
        tasks = generate_daily_tasks(farm, forecast, today=today)
        assert not any(
            task.source_rule
            in {
                "warm_season_greenhouse_start",
                "warm_season_transplant",
                "warm_season_harvest_window",
                "frost_watch_spring",
                "frost_watch_fall",
            }
            for task in tasks
        )


def test_spring_frost_watch_lands_the_month_before_last_frost() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato"],
    )

    march = generate_daily_tasks(
        farm, WeatherForecast(forecast_date=date(2026, 3, 15)), today=date(2026, 3, 15)
    )
    watch = next(task for task in march if task.source_rule == "frost_watch_spring")
    assert watch.severity == TaskSeverity.WATCH


def test_fall_frost_watch_lands_the_month_before_first_frost() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["pepper"],
    )

    october = generate_daily_tasks(
        farm, WeatherForecast(forecast_date=date(2026, 10, 15)), today=date(2026, 10, 15)
    )
    assert any(task.source_rule == "frost_watch_fall" for task in october)


def test_disease_watch_anticipates_wet_weather_in_the_forecast_window() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato"],
    )
    today = date(2026, 6, 26)
    forecast = WeatherForecast(forecast_date=today)
    upcoming = [
        WeatherForecast(forecast_date=date(2026, 6, 27)),
        WeatherForecast(forecast_date=date(2026, 6, 29), heavy_rain_inches=1.1),
    ]

    tasks = generate_daily_tasks(farm, forecast, today=today, upcoming=upcoming)

    watch = next(
        task for task in tasks if task.source_rule == "tomato_wet_weather_disease_watch"
    )
    assert watch.severity == TaskSeverity.WATCH
    assert watch.due_date == today
    assert "Jun 29" in watch.reason


def test_disease_watch_stays_quiet_without_incoming_wet_weather() -> None:
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato"],
    )
    today = date(2026, 6, 26)
    forecast = WeatherForecast(forecast_date=today)
    upcoming = [WeatherForecast(forecast_date=date(2026, 6, 28), heat_index_f=92)]

    tasks = generate_daily_tasks(farm, forecast, today=today, upcoming=upcoming)

    assert not any(
        task.source_rule == "tomato_wet_weather_disease_watch" for task in tasks
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
