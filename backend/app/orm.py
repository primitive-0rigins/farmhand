from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.time import utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    farms: Mapped[list["Farm"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class MagicLink(Base):
    __tablename__ = "magic_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(60))
    planting_zone: Mapped[str] = mapped_column(String(10))
    crops: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    owner: Mapped[User] = relationship(back_populates="farms")
    assets: Mapped[list["FarmAssetRecord"]] = relationship(
        back_populates="farm", cascade="all, delete-orphan"
    )
    spaces: Mapped[list["GrowingSpace"]] = relationship(
        back_populates="farm", cascade="all, delete-orphan"
    )
    plantings: Mapped[list["CropPlanting"]] = relationship(
        back_populates="farm", cascade="all, delete-orphan"
    )


class FarmAssetRecord(Base):
    __tablename__ = "farm_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(60))

    farm: Mapped[Farm] = relationship(back_populates="assets")


class GrowingSpace(Base):
    __tablename__ = "growing_spaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(60))

    farm: Mapped[Farm] = relationship(back_populates="spaces")


class CropPlanting(Base):
    __tablename__ = "crop_plantings"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), index=True)
    crop: Mapped[str] = mapped_column(String(120))
    planted_on: Mapped[date] = mapped_column(Date)

    farm: Mapped[Farm] = relationship(back_populates="plantings")
