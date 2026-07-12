from app.geocode import (
    Coordinates,
    CompositeGeocoder,
    StaticGeocoder,
    coordinates_from_open_meteo,
    coordinates_from_zippopotam,
)


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


def test_zippopotam_reads_first_place() -> None:
    payload = {
        "post code": "29601",
        "places": [
            {"place name": "Greenville", "latitude": "34.8419", "longitude": "-82.4013"}
        ],
    }

    assert coordinates_from_zippopotam(payload) == Coordinates(34.8419, -82.4013)


def test_zippopotam_returns_none_without_places() -> None:
    assert coordinates_from_zippopotam({"places": []}) is None


def test_static_geocoder_normalizes_town_and_zip_keys() -> None:
    geocoder = StaticGeocoder(
        {
            "Greenville, SC": Coordinates(34.85, -82.40),
            "29601": Coordinates(34.8419, -82.4013),
        }
    )

    assert geocoder.locate("greenville,  sc") == Coordinates(34.85, -82.40)
    assert geocoder.locate("29601") == Coordinates(34.8419, -82.4013)
    assert geocoder.locate("Nowhere, SC") is None


def test_composite_geocoder_routes_zip_and_town() -> None:
    zip_geocoder = StaticGeocoder({"29601": Coordinates(34.84, -82.40)})
    town_geocoder = StaticGeocoder({"Piedmont, SC": Coordinates(34.70, -82.46)})
    composite = CompositeGeocoder([zip_geocoder, town_geocoder])

    assert composite.locate("29601") == Coordinates(34.84, -82.40)
    assert composite.locate("Piedmont, SC") == Coordinates(34.70, -82.46)
    assert composite.locate("Unknown") is None
