from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_allowed_origins
from app.domain.models import FarmAsset, FarmProfile, GeneratedTask, TaskSeverity, WeatherForecast
from app.domain.rules import generate_daily_tasks, generate_weekly_plan
from app.schemas import TodayResponse

app = FastAPI(title="Farmhand")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def slug(value: str) -> str:
    normalized = [character.lower() if character.isalnum() else "-" for character in value]
    return "-".join(part for part in "".join(normalized).split("-") if part)


def task_id(task: GeneratedTask) -> str:
    source = task.source_rule or slug(task.title)
    return f"{task.due_date.isoformat()}-{source}-{slug(task.title)}"


def serialize_task(task: GeneratedTask) -> dict[str, object]:
    return {
        "id": task_id(task),
        "title": task.title,
        "due_date": task.due_date.isoformat(),
        "severity": task.severity.value,
        "reason": task.reason,
        "steps": task.steps,
        "source_rule": task.source_rule,
    }


@app.get("/today", response_model=TodayResponse)
def today() -> TodayResponse:
    today_date = date(2026, 6, 26)
    forecasts = [
        WeatherForecast(forecast_date=today_date, heat_index_f=92),
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
    forecast = forecasts[1]
    farm = FarmProfile(
        name="Demo Farm",
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato", "pepper"],
        assets=[
            FarmAsset(name="Main greenhouse", kind="greenhouse"),
            FarmAsset(name="Kubota", kind="tractor"),
            FarmAsset(name="Drip irrigation", kind="irrigation"),
        ],
    )
    upcoming = [item for item in forecasts if item.forecast_date > today_date]
    tasks = generate_daily_tasks(
        farm=farm, forecast=forecast, today=today_date, upcoming=upcoming
    )
    week = generate_weekly_plan(farm=farm, forecasts=forecasts, start_date=today_date)

    return TodayResponse(
        farm={
            "name": farm.name,
            "city": farm.city,
            "state": farm.state,
            "planting_zone": farm.planting_zone,
        },
        today=today_date.isoformat(),
        forecast={
            "date": forecast.forecast_date.isoformat(),
            "summary": "Storms tomorrow, hot afternoons this week",
            "thunderstorm_risk": forecast.thunderstorm_risk,
            "high_wind_mph": forecast.high_wind_mph,
            "heat_index_f": forecast.heat_index_f,
        },
        tasks=[serialize_task(task) for task in tasks],
        week=[
            {
                "date": plan_date.isoformat(),
                "task_count": len(day_tasks),
                "urgent_count": sum(task.severity == TaskSeverity.URGENT for task in day_tasks),
                "watch_count": sum(task.severity == TaskSeverity.WATCH for task in day_tasks),
                "top_task": day_tasks[0].title if day_tasks else None,
            }
            for plan_date, day_tasks in week.items()
        ],
    )
