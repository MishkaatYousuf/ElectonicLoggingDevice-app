"""
Free geocoding via OpenStreetMap Nominatim.
No API key required. Please respect Nominatim's usage policy (max 1 req/sec).
"""
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


class GeocodeError(Exception):
    pass


def geocode(place_name: str):
    """
    Turn a free-text location string into (lat, lng, display_name).
    """
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": place_name, "format": "json", "limit": 1},
        headers={"User-Agent": "eld-trip-planner-hos-app/1.0 (eld_project; mish9758@gmail.com)"},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise GeocodeError(f"Could not find location: {place_name}")

    top = results[0]
    return float(top["lat"]), float(top["lon"]), top.get("display_name", place_name)
