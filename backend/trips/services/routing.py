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
    Returns dict with:
      - distance_miles, duration_hours   (whole route totals)
      - geometry                          (GeoJSON LineString coords [lng,lat])
      - leg_distances_miles               (list, one per leg between waypoints)
      - leg_durations_hours               (list, one per leg between waypoints)
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

    legs = route.get("legs", [])
    leg_distances_miles = [leg["distance"] / 1609.34 for leg in legs]
    leg_durations_hours = [leg["duration"] / 3600 for leg in legs]

    return {
        "distance_miles": distance_meters / 1609.34,
        "duration_hours": duration_seconds / 3600,
        "geometry": route["geometry"]["coordinates"],  # [[lng, lat], ...]
        "leg_distances_miles": leg_distances_miles,
        "leg_durations_hours": leg_durations_hours,
    }