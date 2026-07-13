from contextlib import asynccontextmanager
from datetime import date
from typing import Literal, TypedDict, cast

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.auth import AuthError, logout, request_magic_link, resolve_user, verify_magic_link
from app.config import dev_auth_enabled, get_allowed_origins
from app.db import get_session
from app.domain.models import FarmAsset, FarmProfile, GeneratedTask, Playbook, TaskSeverity
from app.domain.rules import generate_daily_tasks, generate_weekly_plan
from app.email import ConsoleEmailSender, EmailSender
from app.farms import add_asset, add_growing_space, add_planting, delete_asset, delete_growing_space, delete_planting, farm_playbooks, FarmNotFound, create_farm, farm_profile, get_owned_farm, list_farms, save_playbook, save_task_status, task_statuses
from app.geocode import Coordinates, Geocoder, StaticGeocoder
from app.orm import CropPlanting, Farm, FarmAssetRecord, FarmPlaybook, GrowingSpace, User
from app.schemas import (
    FarmCreate,
    FarmAssetCreate,
    FarmAssetResponse,
    FarmResponse,
    FarmPlaybookCreate,
    FarmPlaybookResponse,
    CropPlantingCreate,
    CropPlantingResponse,
    FarmSummary,
    ForecastSummary,
    GrowingSpaceCreate,
    GrowingSpaceResponse,
    MagicLinkRequest,
    MagicLinkResponse,
    SessionResponse,
    TodayResponse,
    TodayTask,
    TaskStatusUpdate,
    UserResponse,
    VerifyRequest,
    WeekDayPlan,
)
from app.weather import DemoWeatherProvider, WeatherProvider

# Swap ConsoleEmailSender() for a real SMTP/transactional sender in production.
email_sender: EmailSender = ConsoleEmailSender()

# Greenville, SC demo coordinates, used as a fallback if geocoding is skipped.
DEMO_LATITUDE = 34.85
DEMO_LONGITUDE = -82.40

# To run live, swap in a keyless geocoder that accepts a town or a ZIP:
#   CompositeGeocoder([ZippopotamGeocoder(), OpenMeteoGeocoder()])
# plus NWSWeatherProvider(). The farm's location then drives a real forecast,
# still with no farmer sign-in.
geocoder: Geocoder = StaticGeocoder(
    {"Greenville, SC": Coordinates(DEMO_LATITUDE, DEMO_LONGITUDE)}
)
weather_provider: WeatherProvider = DemoWeatherProvider()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Farmhand", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


class SerializedTask(TypedDict):
    id: str
    title: str
    due_date: str
    severity: str
    reason: str
    steps: list[str]
    source_rule: str | None


def current_user(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    try:
        return resolve_user(session, authorization)
    except AuthError as error:
        raise HTTPException(status_code=401, detail=str(error))


@app.post("/auth/request", response_model=MagicLinkResponse, status_code=202)
def auth_request(
    body: MagicLinkRequest, session: Session = Depends(get_session)
) -> MagicLinkResponse:
    try:
        token = request_magic_link(session, body.email, email_sender)
    except AuthError as error:
        raise HTTPException(status_code=400, detail=str(error))
    # The token is emailed (logged in dev). It is only echoed here when the
    # dev flag is set, so the flow can be exercised without a mail server.
    return MagicLinkResponse(
        status="sent",
        dev_login_token=token if dev_auth_enabled() else None,
    )


@app.post("/auth/verify", response_model=SessionResponse)
def auth_verify(
    body: VerifyRequest, session: Session = Depends(get_session)
) -> SessionResponse:
    try:
        token = verify_magic_link(session, body.token)
    except AuthError as error:
        raise HTTPException(status_code=401, detail=str(error))
    return SessionResponse(session_token=token)


@app.post("/auth/logout", status_code=204)
def auth_logout(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> None:
    logout(session, authorization)


@app.get("/auth/me", response_model=UserResponse)
def auth_me(user: User = Depends(current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def slug(value: str) -> str:
    normalized = [character.lower() if character.isalnum() else "-" for character in value]
    return "-".join(part for part in "".join(normalized).split("-") if part)


def task_id(task: GeneratedTask) -> str:
    source = task.source_rule or slug(task.title)
    return f"{task.due_date.isoformat()}-{source}-{slug(task.title)}"


def serialize_task(task: GeneratedTask) -> SerializedTask:
    return {
        "id": task_id(task),
        "title": task.title,
        "due_date": task.due_date.isoformat(),
        "severity": task.severity.value,
        "reason": task.reason,
        "steps": task.steps,
        "source_rule": task.source_rule,
    }


def _build_today(
    farm: FarmProfile,
    playbooks: dict[str, Playbook] | None = None,
    statuses: dict[str, str] | None = None,
) -> TodayResponse:
    today_date = date(2026, 6, 26)
    # The farm's town drives the forecast: geocode it, then ask the weather
    # provider for that location. A real deployment stores the coordinates so
    # they are not looked up on every request.
    location = geocoder.locate(f"{farm.city}, {farm.state}") or Coordinates(
        DEMO_LATITUDE, DEMO_LONGITUDE
    )
    forecasts = weather_provider.daily_forecasts(location.latitude, location.longitude)
    forecast = forecasts[1]
    upcoming = [item for item in forecasts if item.forecast_date > today_date]
    tasks = generate_daily_tasks(
        farm=farm, forecast=forecast, today=today_date, playbooks=playbooks, upcoming=upcoming
    )
    week = generate_weekly_plan(
        farm=farm, forecasts=forecasts, start_date=today_date, playbooks=playbooks
    )

    return TodayResponse(
        farm=FarmSummary(
            name=farm.name,
            city=farm.city,
            state=farm.state,
            planting_zone=farm.planting_zone,
        ),
        today=today_date.isoformat(),
        forecast=ForecastSummary(
            date=forecast.forecast_date.isoformat(),
            summary="Storms tomorrow, hot afternoons this week",
            thunderstorm_risk=forecast.thunderstorm_risk,
            high_wind_mph=forecast.high_wind_mph,
            heat_index_f=forecast.heat_index_f,
        ),
        tasks=[
            TodayTask(
                **serialize_task(task),
                status=cast(
                    Literal["open", "completed", "snoozed"],
                    (statuses or {}).get(task_id(task), "open"),
                ),
            )
            for task in tasks
        ],
        week=[
            WeekDayPlan(
                date=plan_date.isoformat(),
                task_count=len(day_tasks),
                urgent_count=sum(task.severity == TaskSeverity.URGENT for task in day_tasks),
                watch_count=sum(task.severity == TaskSeverity.WATCH for task in day_tasks),
                top_task=day_tasks[0].title if day_tasks else None,
            )
            for plan_date, day_tasks in week.items()
        ],
    )


@app.get("/today", response_model=TodayResponse)
def today() -> TodayResponse:
    """Public demo: one showcase farm, no login required."""
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
    return _build_today(farm)


def _farm_response(farm: Farm) -> FarmResponse:
    return FarmResponse(
        id=farm.id,
        name=farm.name,
        city=farm.city,
        state=farm.state,
        planting_zone=farm.planting_zone,
        crops=list(farm.crops),
        assets=[_asset_response(asset) for asset in farm.assets],
        spaces=[_space_response(space) for space in farm.spaces],
        plantings=[_planting_response(planting) for planting in farm.plantings],
        playbooks=[_playbook_response(playbook) for playbook in farm.playbooks],
    )


def _asset_response(asset: FarmAssetRecord) -> FarmAssetResponse:
    return FarmAssetResponse(id=asset.id, name=asset.name, kind=asset.kind)


def _space_response(space: GrowingSpace) -> GrowingSpaceResponse:
    return GrowingSpaceResponse(id=space.id, name=space.name, kind=space.kind)


def _planting_response(planting: CropPlanting) -> CropPlantingResponse:
    return CropPlantingResponse(
        id=planting.id, crop=planting.crop, planted_on=planting.planted_on,
        succession_interval_days=planting.succession_interval_days,
    )


def _playbook_response(playbook: FarmPlaybook) -> FarmPlaybookResponse:
    return FarmPlaybookResponse(
        id=playbook.id,
        trigger=playbook.trigger,
        title=playbook.title,
        steps=list(playbook.steps),
    )


@app.post("/farms", response_model=FarmResponse, status_code=201)
def create_farm_route(
    body: FarmCreate,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> FarmResponse:
    farm = create_farm(
        session,
        user,
        name=body.name,
        city=body.city,
        state=body.state,
        planting_zone=body.planting_zone,
        crops=body.crops,
    )
    return _farm_response(farm)


@app.get("/farms", response_model=list[FarmResponse])
def list_farms_route(
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> list[FarmResponse]:
    return [_farm_response(farm) for farm in list_farms(session, user)]


@app.get("/farms/{farm_id}", response_model=FarmResponse)
def get_farm_route(
    farm_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> FarmResponse:
    try:
        farm = get_owned_farm(session, user, farm_id)
    except FarmNotFound:
        raise HTTPException(status_code=404, detail="farm not found")
    return _farm_response(farm)


@app.post("/farms/{farm_id}/assets", response_model=FarmAssetResponse, status_code=201)
def add_farm_asset_route(
    farm_id: int,
    body: FarmAssetCreate,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> FarmAssetResponse:
    try:
        farm = get_owned_farm(session, user, farm_id)
    except FarmNotFound:
        raise HTTPException(status_code=404, detail="farm not found")
    return _asset_response(add_asset(session, farm, name=body.name, kind=body.kind))


@app.delete("/farms/{farm_id}/assets/{asset_id}", status_code=204)
def delete_farm_asset_route(farm_id: int, asset_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)) -> None:
    try:
        farm = get_owned_farm(session, user, farm_id)
    except FarmNotFound:
        raise HTTPException(status_code=404, detail="farm not found")
    if not delete_asset(session, farm, asset_id):
        raise HTTPException(status_code=404, detail="asset not found")


@app.post("/farms/{farm_id}/spaces", response_model=GrowingSpaceResponse, status_code=201)
def add_growing_space_route(
    farm_id: int,
    body: GrowingSpaceCreate,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> GrowingSpaceResponse:
    try:
        farm = get_owned_farm(session, user, farm_id)
    except FarmNotFound:
        raise HTTPException(status_code=404, detail="farm not found")
    return _space_response(add_growing_space(session, farm, name=body.name, kind=body.kind))


@app.delete("/farms/{farm_id}/spaces/{space_id}", status_code=204)
def delete_growing_space_route(farm_id: int, space_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)) -> None:
    try:
        farm = get_owned_farm(session, user, farm_id)
    except FarmNotFound:
        raise HTTPException(status_code=404, detail="farm not found")
    if not delete_growing_space(session, farm, space_id):
        raise HTTPException(status_code=404, detail="growing space not found")


@app.post("/farms/{farm_id}/plantings", response_model=CropPlantingResponse, status_code=201)
def add_planting_route(
    farm_id: int,
    body: CropPlantingCreate,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> CropPlantingResponse:
    try:
        farm = get_owned_farm(session, user, farm_id)
    except FarmNotFound:
        raise HTTPException(status_code=404, detail="farm not found")
    return _planting_response(
        add_planting(
            session,
            farm,
            crop=body.crop,
            planted_on=body.planted_on,
            succession_interval_days=body.succession_interval_days,
        )
    )


@app.delete("/farms/{farm_id}/plantings/{planting_id}", status_code=204)
def delete_planting_route(farm_id: int, planting_id: int, user: User = Depends(current_user), session: Session = Depends(get_session)) -> None:
    try:
        farm = get_owned_farm(session, user, farm_id)
    except FarmNotFound:
        raise HTTPException(status_code=404, detail="farm not found")
    if not delete_planting(session, farm, planting_id):
        raise HTTPException(status_code=404, detail="planting not found")


@app.post("/farms/{farm_id}/playbooks", response_model=FarmPlaybookResponse, status_code=201)
def save_farm_playbook_route(
    farm_id: int,
    body: FarmPlaybookCreate,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> FarmPlaybookResponse:
    try:
        farm = get_owned_farm(session, user, farm_id)
    except FarmNotFound:
        raise HTTPException(status_code=404, detail="farm not found")
    return _playbook_response(
        save_playbook(session, farm, trigger=body.trigger, title=body.title, steps=body.steps)
    )


@app.post("/farms/{farm_id}/tasks/{task_id}/status", status_code=204)
def save_task_status_route(
    farm_id: int,
    task_id: str,
    body: TaskStatusUpdate,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> None:
    try:
        farm = get_owned_farm(session, user, farm_id)
    except FarmNotFound:
        raise HTTPException(status_code=404, detail="farm not found")
    save_task_status(session, farm, task_id=task_id, status=body.status)


@app.get("/farms/{farm_id}/today", response_model=TodayResponse)
def farm_today_route(
    farm_id: int,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> TodayResponse:
    try:
        farm = get_owned_farm(session, user, farm_id)
    except FarmNotFound:
        raise HTTPException(status_code=404, detail="farm not found")
    return _build_today(farm_profile(farm), farm_playbooks(farm), task_statuses(farm))
