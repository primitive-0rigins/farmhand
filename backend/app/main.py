from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_allowed_origins
from app.domain.models import FarmAsset, FarmProfile, GeneratedTask, TaskSeverity
from app.domain.rules import generate_daily_tasks, generate_weekly_plan
from app.geocode import Coordinates, Geocoder, StaticGeocoder
from app.schemas import TodayResponse
from app.weather import DemoWeatherProvider, WeatherProvider

# Greenville, SC demo coordinates, used as a fallback if geocoding is skipped.
DEMO_LATITUDE = 34.85
DEMO_LONGITUDE = -82.40

# Swap these for OpenMeteoGeocoder() and NWSWeatherProvider() to run live:
# the farm's town then drives a real forecast, still with no farmer sign-in.
geocoder: Geocoder = StaticGeocoder(
    {("Greenville", "SC"): Coordinates(DEMO_LATITUDE, DEMO_LONGITUDE)}
)
weather_provider: WeatherProvider = DemoWeatherProvider()

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
    # The farm's town drives the forecast: geocode it once, then ask the
    # weather provider for that location. A real deployment stores the result
    # so it is not looked up on every request.
    location = geocoder.locate(farm.city, farm.state) or Coordinates(
        DEMO_LATITUDE, DEMO_LONGITUDE
    )
    forecasts = weather_provider.daily_forecasts(location.latitude, location.longitude)
    forecast = forecasts[1]
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
