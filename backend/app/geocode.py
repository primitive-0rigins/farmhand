from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Open-Meteo's geocoding API is free and keyless: it turns a town name into
# coordinates and returns the state, so we can tell apart the many towns that
# share a name. Like the weather provider, no farmer credentials are involved.
OPEN_METEO_GEOCODER = "https://geocoding-api.open-meteo.com/v1/search"
GEOCODER_USER_AGENT = "farmhand-demo (contact@example.com)"

# Abbreviation -> full name, so a farm's "SC" matches the geocoder's
# "South Carolina" when a town name appears in more than one state.
US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


class Geocoder(Protocol):
    """Turns a farm's town into coordinates. Returns None if it can't be found."""

    def locate(self, city: str, state: str) -> Coordinates | None:
        ...


class StaticGeocoder:
    """Offline geocoder for the demo and tests."""

    def __init__(self, places: dict[tuple[str, str], Coordinates]):
        self._places = {
            (city.lower(), state.lower()): coords
            for (city, state), coords in places.items()
        }

    def locate(self, city: str, state: str) -> Coordinates | None:
        return self._places.get((city.lower(), state.lower()))


class OpenMeteoGeocoder:
    """Free, keyless town geocoder (open-meteo.com)."""

    def locate(self, city: str, state: str) -> Coordinates | None:
        query = urlencode(
            {"name": city, "count": 10, "language": "en", "format": "json"}
        )
        request = Request(
            f"{OPEN_METEO_GEOCODER}?{query}",
            headers={"User-Agent": GEOCODER_USER_AGENT},
        )
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
        return coordinates_from_open_meteo(payload, state)


def coordinates_from_open_meteo(payload: dict, state: str) -> Coordinates | None:
    """Pick the US result that matches the farm's state, else the first US hit."""
    results = [
        result
        for result in payload.get("results", [])
        if result.get("country_code") == "US"
    ]
    if not results:
        return None

    state_name = US_STATES.get(state.upper(), state).lower()
    for result in results:
        if (result.get("admin1") or "").lower() == state_name:
            return Coordinates(result["latitude"], result["longitude"])

    first = results[0]
    return Coordinates(first["latitude"], first["longitude"])
