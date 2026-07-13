import pytest

from app.farms import (
    FarmNotFound,
    create_farm,
    farm_profile,
    get_owned_farm,
    list_farms,
)
from app.orm import User


def _make_user(db, email: str) -> User:
    user = User(email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_farm(db, user: User, name: str = "Home Farm"):
    return create_farm(
        db,
        user,
        name=name,
        city="Greenville",
        state="SC",
        planting_zone="8b",
        crops=["tomato", "pepper"],
    )


def test_farm_is_owned_by_its_creator(db) -> None:
    user = _make_user(db, "farmer@example.com")
    farm = _make_farm(db, user)

    assert farm.user_id == user.id
    assert get_owned_farm(db, user, farm.id).id == farm.id


def test_list_returns_only_the_users_own_farms(db) -> None:
    alice = _make_user(db, "alice@example.com")
    bob = _make_user(db, "bob@example.com")
    _make_farm(db, alice, "Alice Farm")
    _make_farm(db, bob, "Bob Farm")

    alice_farms = list_farms(db, alice)
    assert [farm.name for farm in alice_farms] == ["Alice Farm"]


def test_a_user_cannot_read_another_users_farm(db) -> None:
    alice = _make_user(db, "alice@example.com")
    bob = _make_user(db, "bob@example.com")
    bob_farm = _make_farm(db, bob, "Bob Farm")

    with pytest.raises(FarmNotFound):
        get_owned_farm(db, alice, bob_farm.id)


def test_missing_farm_is_not_found(db) -> None:
    user = _make_user(db, "farmer@example.com")

    with pytest.raises(FarmNotFound):
        get_owned_farm(db, user, 999)


def test_farm_profile_maps_to_domain_type(db) -> None:
    user = _make_user(db, "farmer@example.com")
    farm = _make_farm(db, user)

    profile = farm_profile(farm)
    assert profile.planting_zone == "8b"
    assert "tomato" in profile.crops
    assert profile.assets == []
