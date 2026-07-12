from datetime import date

from app.weather import DemoWeatherProvider, forecasts_from_nws_periods


def _period(start, *, daytime, temp, wind, short):
    return {
        "startTime": start,
        "isDaytime": daytime,
        "temperature": temp,
        "windSpeed": wind,
        "shortForecast": short,
    }


def test_nws_periods_map_into_daily_forecasts() -> None:
    periods = [
        _period(
            "2026-04-10T06:00:00-04:00",
            daytime=True,
            temp=68,
            wind="10 to 20 mph",
            short="Chance Showers And Thunderstorms",
        ),
        _period(
            "2026-04-10T18:00:00-04:00",
            daytime=False,
            temp=34,
            wind="5 mph",
            short="Clear",
        ),
        _period(
            "2026-04-11T06:00:00-04:00",
            daytime=True,
            temp=75,
            wind="5 to 10 mph",
            short="Sunny",
        ),
    ]

    forecasts = forecasts_from_nws_periods(periods)

    assert [f.forecast_date for f in forecasts] == [
        date(2026, 4, 10),
        date(2026, 4, 11),
    ]

    day_one = forecasts[0]
    assert day_one.thunderstorm_risk is True
    assert day_one.frost_risk is True  # 34F overnight
    assert day_one.high_wind_mph == 20
    assert day_one.heat_index_f == 68  # daytime high

    day_two = forecasts[1]
    assert day_two.thunderstorm_risk is False
    assert day_two.frost_risk is False


def test_demo_provider_returns_a_week_with_the_storm_day() -> None:
    forecasts = DemoWeatherProvider().daily_forecasts(34.85, -82.40)

    assert len(forecasts) == 7
    assert any(f.thunderstorm_risk for f in forecasts)
