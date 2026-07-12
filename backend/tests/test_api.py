from app.main import today


def test_today_endpoint_payload_contains_generated_tasks() -> None:
    payload = today()

    assert payload.farm.name == "Demo Farm"
    assert payload.forecast.thunderstorm_risk is True
    assert len(payload.tasks) == 4
    assert any(task.source_rule == "bad_weather_playbook" for task in payload.tasks)
    assert any(task.source_rule == "heat_irrigation_playbook" for task in payload.tasks)
    assert len(payload.week) == 7
    assert payload.week[0].date == payload.today
    assert any(day.urgent_count > 0 for day in payload.week)
