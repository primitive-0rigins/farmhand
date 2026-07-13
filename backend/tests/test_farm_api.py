from fastapi.testclient import TestClient

from app.auth import request_magic_link, verify_magic_link
from app.db import get_session
from app.main import app
from tests.conftest import RecordingEmailSender


def _authorization(db, email: str) -> dict[str, str]:
    sender = RecordingEmailSender()
    request_magic_link(db, email, sender)
    assert sender.last_token is not None
    token = verify_magic_link(db, sender.last_token)
    return {"Authorization": f"Bearer {token}"}


def test_farm_routes_require_authentication(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        response = TestClient(app).get("/farms")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


def test_farmer_can_create_list_and_plan_for_their_farm(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        response = client.post(
            "/farms",
            headers=_authorization(db, "farmer@example.com"),
            json={
                "name": "South Field",
                "city": "Greenville",
                "state": "SC",
                "planting_zone": "8b",
                "crops": ["tomato"],
            },
        )
        farm = response.json()
        listed = client.get("/farms", headers=_authorization(db, "farmer@example.com"))
        today = client.get(
            f"/farms/{farm['id']}/today", headers=_authorization(db, "farmer@example.com")
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert listed.json() == [farm]
    assert today.status_code == 200
    assert today.json()["farm"]["name"] == "South Field"
    assert any(
        task["source_rule"] == "tomato_summer_scouting"
        for task in today.json()["tasks"]
    )


def test_recorded_assets_change_the_farm_plan(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        farm = client.post(
            "/farms",
            headers=headers,
            json={
                "name": "South Field",
                "city": "Greenville",
                "state": "SC",
                "planting_zone": "8b",
                "crops": [],
            },
        ).json()
        tractor = client.post(
            f"/farms/{farm['id']}/assets",
            headers=headers,
            json={"name": "Kubota", "kind": "tractor"},
        )
        irrigation = client.post(
            f"/farms/{farm['id']}/assets",
            headers=headers,
            json={"name": "Drip irrigation", "kind": " Irrigation "},
        )
        today = client.get(f"/farms/{farm['id']}/today", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert tractor.status_code == 201
    assert irrigation.status_code == 201
    assert irrigation.json()["kind"] == "irrigation"
    assert any(
        task["source_rule"] == "heat_irrigation_playbook" for task in today.json()["tasks"]
    )
    weather_task = next(
        task for task in today.json()["tasks"] if task["source_rule"] == "bad_weather_playbook"
    )
    assert "Make sure tractor and implements are covered or parked safely." in weather_task["steps"]


def test_farmer_can_record_a_growing_space(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        farm = client.post(
            "/farms",
            headers=headers,
            json={"name": "South Field", "city": "Greenville", "state": "SC", "planting_zone": "8b"},
        ).json()
        created = client.post(
            f"/farms/{farm['id']}/spaces",
            headers=headers,
            json={"name": "North tunnel", "kind": "high_tunnel"},
        )
        stored = client.get(f"/farms/{farm['id']}", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert stored.json()["spaces"] == [created.json()]


def test_farmer_can_record_a_crop_planting(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        farm = client.post(
            "/farms",
            headers=headers,
            json={"name": "South Field", "city": "Greenville", "state": "SC", "planting_zone": "8b"},
        ).json()
        created = client.post(
            f"/farms/{farm['id']}/plantings",
            headers=headers,
            json={"crop": " Tomato ", "planted_on": "2026-04-20"},
        )
        stored = client.get(f"/farms/{farm['id']}", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["crop"] == "tomato"
    assert stored.json()["plantings"] == [created.json()]


def test_saved_playbook_changes_the_farms_weather_task(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        farm = client.post(
            "/farms",
            headers=headers,
            json={"name": "South Field", "city": "Greenville", "state": "SC", "planting_zone": "8b"},
        ).json()
        saved = client.post(
            f"/farms/{farm['id']}/playbooks",
            headers=headers,
            json={
                "trigger": "bad_weather",
                "title": "Storm checklist",
                "steps": ["Latch the tunnel.", "Cover the tractor."],
            },
        )
        today = client.get(f"/farms/{farm['id']}/today", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert saved.status_code == 201
    task = next(task for task in today.json()["tasks"] if task["source_rule"] == "bad_weather_playbook")
    assert task["title"] == "Storm checklist"
    assert task["steps"] == ["Latch the tunnel.", "Cover the tractor."]


def test_task_status_persists_for_a_farm(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        farm = client.post(
            "/farms",
            headers=headers,
            json={"name": "South Field", "city": "Greenville", "state": "SC", "planting_zone": "8b"},
        ).json()
        today = client.get(f"/farms/{farm['id']}/today", headers=headers).json()
        task_id = today["tasks"][0]["id"]
        saved = client.post(
            f"/farms/{farm['id']}/tasks/{task_id}/status",
            headers=headers,
            json={"status": "completed"},
        )
        refreshed = client.get(f"/farms/{farm['id']}/today", headers=headers).json()
    finally:
        app.dependency_overrides.clear()

    assert saved.status_code == 204
    assert next(task for task in refreshed["tasks"] if task["id"] == task_id)["status"] == "completed"


def test_manual_task_persists_in_a_farms_today_feed(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        farm = client.post(
            "/farms",
            headers=headers,
            json={"name": "South Field", "city": "Greenville", "state": "SC", "planting_zone": "8b"},
        ).json()
        today = client.get(f"/farms/{farm['id']}/today", headers=headers).json()
        created = client.post(
            f"/farms/{farm['id']}/manual-tasks",
            headers=headers,
            json={"title": "Check row cover", "reason": "Wind is expected.", "due_date": today["today"]},
        )
        refreshed = client.get(f"/farms/{farm['id']}/today", headers=headers).json()
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["title"] == "Check row cover"
    assert any(
        task["id"] == f"manual-{created.json()['id']}"
        and task["reason"] == "Wind is expected."
        for task in refreshed["tasks"]
    )


def test_farmer_can_remove_a_manual_task(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        farm = client.post(
            "/farms",
            headers=headers,
            json={"name": "South Field", "city": "Greenville", "state": "SC", "planting_zone": "8b"},
        ).json()
        today = client.get(f"/farms/{farm['id']}/today", headers=headers).json()
        task = client.post(
            f"/farms/{farm['id']}/manual-tasks",
            headers=headers,
            json={"title": "Check row cover", "reason": "Wind is expected.", "due_date": today["today"]},
        ).json()
        deleted = client.delete(f"/farms/{farm['id']}/manual-tasks/{task['id']}", headers=headers)
        refreshed = client.get(f"/farms/{farm['id']}/today", headers=headers).json()
    finally:
        app.dependency_overrides.clear()

    assert deleted.status_code == 204
    assert not any(item["id"] == f"manual-{task['id']}" for item in refreshed["tasks"])


def test_farmer_can_remove_their_setup_records(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        farm = client.post(
            "/farms",
            headers=headers,
            json={"name": "South Field", "city": "Greenville", "state": "SC", "planting_zone": "8b"},
        ).json()
        asset = client.post(f"/farms/{farm['id']}/assets", headers=headers, json={"name": "Drip", "kind": "irrigation"}).json()
        space = client.post(f"/farms/{farm['id']}/spaces", headers=headers, json={"name": "North field", "kind": "field"}).json()
        planting = client.post(f"/farms/{farm['id']}/plantings", headers=headers, json={"crop": "lettuce", "planted_on": "2026-04-01"}).json()
        responses = [
            client.delete(f"/farms/{farm['id']}/assets/{asset['id']}", headers=headers),
            client.delete(f"/farms/{farm['id']}/spaces/{space['id']}", headers=headers),
            client.delete(f"/farms/{farm['id']}/plantings/{planting['id']}", headers=headers),
        ]
        stored = client.get(f"/farms/{farm['id']}", headers=headers).json()
    finally:
        app.dependency_overrides.clear()

    assert [response.status_code for response in responses] == [204, 204, 204]
    assert stored["assets"] == []
    assert stored["spaces"] == []
    assert stored["plantings"] == []


def test_farmer_can_correct_their_setup_records(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        farm = client.post(
            "/farms",
            headers=headers,
            json={"name": "South Field", "city": "Greenville", "state": "SC", "planting_zone": "8b"},
        ).json()
        asset = client.post(f"/farms/{farm['id']}/assets", headers=headers, json={"name": "Drip", "kind": "irrigation"}).json()
        space = client.post(f"/farms/{farm['id']}/spaces", headers=headers, json={"name": "North field", "kind": "field"}).json()
        planting = client.post(f"/farms/{farm['id']}/plantings", headers=headers, json={"crop": "lettuce", "planted_on": "2026-04-01"}).json()
        updated = [
            client.put(f"/farms/{farm['id']}/assets/{asset['id']}", headers=headers, json={"name": "West drip", "kind": " Irrigation "}),
            client.put(f"/farms/{farm['id']}/spaces/{space['id']}", headers=headers, json={"name": "North tunnel", "kind": "high_tunnel"}),
            client.put(f"/farms/{farm['id']}/plantings/{planting['id']}", headers=headers, json={"crop": " Lettuce ", "planted_on": "2026-04-05", "succession_interval_days": 14}),
        ]
        stored = client.get(f"/farms/{farm['id']}", headers=headers).json()
    finally:
        app.dependency_overrides.clear()

    assert [response.status_code for response in updated] == [200, 200, 200]
    assert stored["assets"] == [{"id": asset["id"], "name": "West drip", "kind": "irrigation"}]
    assert stored["spaces"] == [{"id": space["id"], "name": "North tunnel", "kind": "high_tunnel"}]
    assert stored["plantings"] == [{"id": planting["id"], "crop": "lettuce", "planted_on": "2026-04-05", "succession_interval_days": 14}]


def test_farmer_can_export_their_farm_data(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        farm = client.post(
            "/farms",
            headers=headers,
            json={"name": "South Field", "city": "Greenville", "state": "SC", "planting_zone": "8b", "crops": ["tomato"]},
        ).json()
        task = client.post(
            f"/farms/{farm['id']}/manual-tasks",
            headers=headers,
            json={"title": "Check row cover", "reason": "Wind is expected.", "due_date": "2026-06-26"},
        ).json()
        response = client.get(f"/farms/{farm['id']}/export", headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-disposition"] == f'attachment; filename="farmhand-farm-{farm["id"]}.json"'
    assert response.json()["farm"]["crops"] == ["tomato"]
    assert response.json()["task_states"] == []
    assert response.json()["manual_tasks"] == [task]


def test_farmer_cannot_read_another_users_farm(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        owner_headers = _authorization(db, "owner@example.com")
        farm = client.post(
            "/farms",
            headers=owner_headers,
            json={
                "name": "Owner Farm",
                "city": "Greenville",
                "state": "SC",
                "planting_zone": "8b",
                "crops": [],
            },
        ).json()
        response = client.get(
            f"/farms/{farm['id']}", headers=_authorization(db, "other@example.com")
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_farm_creation_rejects_blank_fields_and_normalizes_crops(db) -> None:
    app.dependency_overrides[get_session] = lambda: db
    try:
        client = TestClient(app)
        headers = _authorization(db, "farmer@example.com")
        invalid = client.post(
            "/farms",
            headers=headers,
            json={
                "name": " ",
                "city": "Greenville",
                "state": "SC",
                "planting_zone": "8b",
                "crops": [],
            },
        )
        created = client.post(
            "/farms",
            headers=headers,
            json={
                "name": "  South Field  ",
                "city": " Greenville ",
                "state": " SC ",
                "planting_zone": " 8b ",
                "crops": [" Tomato ", "tomato", "PEPPER"],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert invalid.status_code == 422
    assert created.json() == {
        "id": 1,
        "name": "South Field",
        "city": "Greenville",
        "state": "SC",
        "planting_zone": "8b",
        "crops": ["tomato", "pepper"],
        "assets": [],
        "spaces": [],
        "plantings": [],
        "playbooks": [],
    }
