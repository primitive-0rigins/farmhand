from app.main import today


def test_today_endpoint_payload_contains_generated_tasks() -> None:
    payload = today()

    assert payload.farm.name == "Demo Farm"
    assert payload.forecast.thunderstorm_risk is True
    assert len(payload.tasks) == 4
    assert any(task.source_rule == "bad_weather_playbook" for task in payload.tasks)
    assert any(task.source_rule == "heat_irrigation_playbook" for task in payload.tasks)
