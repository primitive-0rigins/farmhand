from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import FarmProfile
from app.orm import Farm, User


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


def farm_profile(farm: Farm) -> FarmProfile:
    """Map the stored farm onto the domain type the rules operate on.

    Assets are not persisted yet, so asset-gated rules stay quiet until a
    farm records equipment.
    """
    return FarmProfile(
        name=farm.name,
        city=farm.city,
        state=farm.state,
        planting_zone=farm.planting_zone,
        crops=list(farm.crops),
    )
