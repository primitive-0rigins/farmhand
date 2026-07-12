from app.config import DEFAULT_ALLOWED_ORIGINS, get_allowed_origins


def test_allowed_origins_default_to_local_dev(monkeypatch) -> None:
    monkeypatch.delenv("FARMHAND_ALLOWED_ORIGINS", raising=False)

    assert get_allowed_origins() == list(DEFAULT_ALLOWED_ORIGINS)


def test_allowed_origins_read_comma_separated_env(monkeypatch) -> None:
    monkeypatch.setenv(
        "FARMHAND_ALLOWED_ORIGINS",
        "https://farmhand.example.com, https://app.farmhand.example.com",
    )

    assert get_allowed_origins() == [
        "https://farmhand.example.com",
        "https://app.farmhand.example.com",
    ]
