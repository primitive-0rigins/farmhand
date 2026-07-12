from datetime import date

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_allowed_origins
from app.domain.models import FarmAsset, FarmProfile, WeatherForecast
from app.domain.rules import generate_daily_tasks
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


@app.get("/today", response_model=TodayResponse)
def today() -> TodayResponse:
    today_date = date(2026, 6, 26)
    forecast = WeatherForecast(
        forecast_date=date(2026, 6, 27),
        thunderstorm_risk=True,
        high_wind_mph=34,
        heat_index_f=92,
    )
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
    tasks = generate_daily_tasks(farm=farm, forecast=forecast, today=today_date)

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
        tasks=[
            {
                "id": task.source_rule or task.title.lower().replace(" ", "-"),
                "title": task.title,
                "due_date": task.due_date.isoformat(),
                "severity": task.severity.value,
                "reason": task.reason,
                "steps": task.steps,
                "source_rule": task.source_rule,
            }
            for task in tasks
        ],
    )
