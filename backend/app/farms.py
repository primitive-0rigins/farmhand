from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import CropPlanting as DomainCropPlanting, FarmAsset, FarmProfile, Playbook
from app.orm import CropPlanting, Farm, FarmAssetRecord, FarmManualTask, FarmPlaybook, FarmTaskState, GrowingSpace, User


class FarmNotFound(Exception):
    """Raised when a farm does not exist or is not owned by the caller."""


def create_farm(
    session: Session,
    user: User,
    *,
    name: str,
    city: str,
    state: str,
    planting_zone: str,
    crops: Sequence[str],
) -> Farm:
    farm = Farm(
        user_id=user.id,
        name=name,
        city=city,
        state=state,
        planting_zone=planting_zone,
        crops=list(crops),
    )
    session.add(farm)
    session.commit()
    session.refresh(farm)
    return farm


def list_farms(session: Session, user: User) -> list[Farm]:
    return list(
        session.scalars(
            select(Farm).where(Farm.user_id == user.id).order_by(Farm.id)
        )
    )


def get_owned_farm(session: Session, user: User, farm_id: int) -> Farm:
    """Return the farm only if the caller owns it.

    A farm owned by someone else is reported as not found rather than
    forbidden, so the endpoint does not leak that the id exists.
    """
    farm = session.get(Farm, farm_id)
    if farm is None or farm.user_id != user.id:
        raise FarmNotFound("farm not found")
    return farm


def add_asset(session: Session, farm: Farm, *, name: str, kind: str) -> FarmAssetRecord:
    asset = FarmAssetRecord(farm_id=farm.id, name=name, kind=kind)
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return asset


def update_asset(
    session: Session, farm: Farm, asset_id: int, *, name: str, kind: str
) -> FarmAssetRecord | None:
    asset = session.get(FarmAssetRecord, asset_id)
    if asset is None or asset.farm_id != farm.id:
        return None
    asset.name = name
    asset.kind = kind
    session.commit()
    session.refresh(asset)
    return asset


def add_growing_space(session: Session, farm: Farm, *, name: str, kind: str) -> GrowingSpace:
    space = GrowingSpace(farm_id=farm.id, name=name, kind=kind)
    session.add(space)
    session.commit()
    session.refresh(space)
    return space


def update_growing_space(
    session: Session, farm: Farm, space_id: int, *, name: str, kind: str
) -> GrowingSpace | None:
    space = session.get(GrowingSpace, space_id)
    if space is None or space.farm_id != farm.id:
        return None
    space.name = name
    space.kind = kind
    session.commit()
    session.refresh(space)
    return space


def add_planting(session: Session, farm: Farm, *, crop: str, planted_on: date, succession_interval_days: int | None) -> CropPlanting:
    planting = CropPlanting(farm_id=farm.id, crop=crop, planted_on=planted_on, succession_interval_days=succession_interval_days)
    session.add(planting)
    session.commit()
    session.refresh(planting)
    return planting


def update_planting(
    session: Session,
    farm: Farm,
    planting_id: int,
    *,
    crop: str,
    planted_on: date,
    succession_interval_days: int | None,
) -> CropPlanting | None:
    planting = session.get(CropPlanting, planting_id)
    if planting is None or planting.farm_id != farm.id:
        return None
    planting.crop = crop
    planting.planted_on = planted_on
    planting.succession_interval_days = succession_interval_days
    session.commit()
    session.refresh(planting)
    return planting


def save_playbook(
    session: Session, farm: Farm, *, trigger: str, title: str, steps: Sequence[str]
) -> FarmPlaybook:
    playbook = session.scalar(
        select(FarmPlaybook).where(
            FarmPlaybook.farm_id == farm.id, FarmPlaybook.trigger == trigger
        )
    )
    if playbook is None:
        playbook = FarmPlaybook(farm_id=farm.id, trigger=trigger, title=title, steps=list(steps))
        session.add(playbook)
    else:
        playbook.title = title
        playbook.steps = list(steps)
    session.commit()
    session.refresh(playbook)
    return playbook


def farm_playbooks(farm: Farm) -> dict[str, Playbook]:
    return {
        playbook.trigger: Playbook(
            trigger=playbook.trigger, title=playbook.title, steps=list(playbook.steps)
        )
        for playbook in farm.playbooks
    }


def task_statuses(farm: Farm) -> dict[str, str]:
    return {state.task_id: state.status for state in farm.task_states}


def save_task_status(session: Session, farm: Farm, *, task_id: str, status: str) -> None:
    state = session.scalar(
        select(FarmTaskState).where(
            FarmTaskState.farm_id == farm.id, FarmTaskState.task_id == task_id
        )
    )
    if status == "open":
        if state is not None:
            session.delete(state)
    elif state is None:
        session.add(FarmTaskState(farm_id=farm.id, task_id=task_id, status=status))
    else:
        state.status = status
    session.commit()


def add_manual_task(
    session: Session, farm: Farm, *, title: str, reason: str, due_date: date
) -> FarmManualTask:
    task = FarmManualTask(farm_id=farm.id, title=title, reason=reason, due_date=due_date)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_asset(session: Session, farm: Farm, asset_id: int) -> bool:
    asset = session.get(FarmAssetRecord, asset_id)
    if asset is None or asset.farm_id != farm.id:
        return False
    session.delete(asset)
    session.commit()
    return True


def delete_growing_space(session: Session, farm: Farm, space_id: int) -> bool:
    space = session.get(GrowingSpace, space_id)
    if space is None or space.farm_id != farm.id:
        return False
    session.delete(space)
    session.commit()
    return True


def delete_planting(session: Session, farm: Farm, planting_id: int) -> bool:
    planting = session.get(CropPlanting, planting_id)
    if planting is None or planting.farm_id != farm.id:
        return False
    session.delete(planting)
    session.commit()
    return True


def farm_profile(farm: Farm) -> FarmProfile:
    """Map the stored farm onto the domain type the rules operate on.

    Asset-backed rules use the farm's recorded equipment.
    """
    return FarmProfile(
        name=farm.name,
        city=farm.city,
        state=farm.state,
        planting_zone=farm.planting_zone,
        crops=list(farm.crops),
        assets=[FarmAsset(name=asset.name, kind=asset.kind) for asset in farm.assets],
        plantings=[DomainCropPlanting(crop=planting.crop, planted_on=planting.planted_on, succession_interval_days=planting.succession_interval_days) for planting in farm.plantings],
    )
