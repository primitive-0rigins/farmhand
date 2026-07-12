from app.geocode import Coordinates, StaticGeocoder, coordinates_from_open_meteo


def test_open_meteo_result_is_disambiguated_by_state() -> None:
    payload = {
        "results": [
            {
                "name": "Piedmont",
                "latitude": 37.82,
                "longitude": -122.23,
                "country_code": "US",
                "admin1": "California",
            },
            {
                "name": "Piedmont",
                "latitude": 34.70,
                "longitude": -82.46,
                "country_code": "US",
                "admin1": "South Carolina",
            },
        ]
    }

    coords = coordinates_from_open_meteo(payload, "SC")

    assert coords == Coordinates(34.70, -82.46)


def test_open_meteo_falls_back_to_first_us_result() -> None:
    payload = {
        "results": [
            {
                "name": "Springfield",
                "latitude": 39.80,
                "longitude": -89.64,
                "country_code": "US",
                "admin1": "Illinois",
            }
        ]
    }

    coords = coordinates_from_open_meteo(payload, "ZZ")

    assert coords == Coordinates(39.80, -89.64)


def test_open_meteo_returns_none_without_us_results() -> None:
    assert coordinates_from_open_meteo({"results": []}, "SC") is None


def test_static_geocoder_matches_case_insensitively() -> None:
    geocoder = StaticGeocoder({("Greenville", "SC"): Coordinates(34.85, -82.40)})

    assert geocoder.locate("greenville", "sc") == Coordinates(34.85, -82.40)
    assert geocoder.locate("Nowhere", "SC") is None
