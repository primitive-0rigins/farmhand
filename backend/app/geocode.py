from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Both geocoding services below are free and keyless: a farmer enters one
# "where's your farm?" field -- a town or a ZIP -- and nothing else. No API
# key, no account, no sign-in.
OPEN_METEO_GEOCODER = "https://geocoding-api.open-meteo.com/v1/search"
ZIPPOPOTAM_API = "https://api.zippopotam.us/us"
GEOCODER_USER_AGENT = "farmhand-demo (contact@example.com)"

_ZIP_RE = re.compile(r"^\d{5}$")

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
    """Turns a farm's location (a town or a ZIP) into coordinates, or None."""

    def locate(self, location: str) -> Coordinates | None:
        ...


class StaticGeocoder:
    """Offline geocoder for the demo and tests. Keyed by the location string."""

    def __init__(self, places: dict[str, Coordinates]):
        self._places = {self._key(name): coords for name, coords in places.items()}

    def locate(self, location: str) -> Coordinates | None:
        return self._places.get(self._key(location))

    @staticmethod
    def _key(location: str) -> str:
        return " ".join(location.lower().replace(",", " ").split())


class OpenMeteoGeocoder:
    """Free, keyless town geocoder. Handles 'City' or 'City, ST'."""

    def locate(self, location: str) -> Coordinates | None:
        if _ZIP_RE.match(location.strip()):
            return None  # a bare ZIP; leave it to a ZIP geocoder
        city, _, state = location.partition(",")
        query = urlencode(
            {"name": city.strip(), "count": 10, "language": "en", "format": "json"}
        )
        request = Request(
            f"{OPEN_METEO_GEOCODER}?{query}",
            headers={"User-Agent": GEOCODER_USER_AGENT},
        )
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
        return coordinates_from_open_meteo(payload, state.strip())


class ZippopotamGeocoder:
    """Free, keyless US ZIP-code geocoder (zippopotam.us)."""

    def locate(self, location: str) -> Coordinates | None:
        zip_code = location.strip()
        if not _ZIP_RE.match(zip_code):
            return None  # not a ZIP; leave it to a town geocoder
        request = Request(
            f"{ZIPPOPOTAM_API}/{zip_code}",
            headers={"User-Agent": GEOCODER_USER_AGENT},
        )
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.load(response)
        except HTTPError:
            return None  # unknown ZIP returns 404
        return coordinates_from_zippopotam(payload)


class CompositeGeocoder:
    """Tries each geocoder in order and returns the first hit (ZIP or town)."""

    def __init__(self, geocoders: list[Geocoder]):
        self._geocoders = geocoders

    def locate(self, location: str) -> Coordinates | None:
        for geocoder in self._geocoders:
            coords = geocoder.locate(location)
            if coords is not None:
                return coords
        return None


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


def coordinates_from_zippopotam(payload: dict) -> Coordinates | None:
    """Read the first place in a zippopotam.us response (lat/lon come as text)."""
    places = payload.get("places") or []
    if not places:
        return None
    place = places[0]
    try:
        return Coordinates(float(place["latitude"]), float(place["longitude"]))
    except (KeyError, ValueError):
        return None
