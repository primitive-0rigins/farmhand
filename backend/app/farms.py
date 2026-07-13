from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import FarmAsset, FarmProfile
from app.orm import Farm, FarmAssetRecord, User


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
    )
