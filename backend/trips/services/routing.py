"""
Free routing via OSRM's public demo server (no API key required).
http://project-osrm.org/docs/v5.24.0/api/#route-service
"""
import requests

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"


class RoutingError(Exception):
    pass


def get_route(waypoints):
    """
    waypoints: list of (lat, lng) tuples, in visiting order.
    Returns dict with distance_miles, duration_hours, geometry (GeoJSON LineString coords [lng,lat]).
    """
    coord_str = ";".join(f"{lng},{lat}" for lat, lng in waypoints)
    url = f"{OSRM_BASE_URL}/{coord_str}"

    resp = requests.get(
        url,
        params={"overview": "full", "geometries": "geojson"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError(f"Could not compute route: {data.get('message', 'unknown error')}")

    route = data["routes"][0]
    distance_meters = route["distance"]
    duration_seconds = route["duration"]

    return {
        "distance_miles": distance_meters / 1609.34,
        "duration_hours": duration_seconds / 3600,
        "geometry": route["geometry"]["coordinates"],  # [[lng, lat], ...]
    }
