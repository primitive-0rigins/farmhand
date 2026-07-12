from datetime import date

from app.domain.models import GeneratedTask, TaskSeverity
from app.main import serialize_task, today


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


def test_today_endpoint_task_ids_are_unique() -> None:
    payload = today()

    task_ids = [task.id for task in payload.tasks]

    assert len(task_ids) == len(set(task_ids))


def test_serialized_task_id_includes_date_rule_and_title_slug() -> None:
    task = GeneratedTask(
        title="Scout tomatoes for leaf disease after wet weather.",
        due_date=date(2026, 6, 29),
        severity=TaskSeverity.WATCH,
        reason="Heavy rain raises disease pressure.",
        source_rule="tomato_wet_weather_disease_pressure",
    )

    serialized = serialize_task(task)

    assert (
        serialized["id"]
        == "2026-06-29-tomato_wet_weather_disease_pressure-scout-tomatoes-for-leaf-disease-after-wet-weather"
    )
