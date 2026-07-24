import {
  MapContainer,
  TileLayer,
  Polyline,
  CircleMarker,
  Tooltip,
} from "react-leaflet";
import { useMemo } from "react";
import "./MapView.css";

const STOP_COLORS = {
  PICKUP: "#34d399",
  DROPOFF: "#e5484d",
  FUEL: "#5b9dd9",
  REST_BREAK: "#ffb627",
  OVERNIGHT: "#a78bfa",
  RESTART_34: "#f472b6",
};

const STOP_LABELS = {
  PICKUP: "Pickup",
  DROPOFF: "Drop-off",
  FUEL: "Fuel stop",
  REST_BREAK: "30-min break",
  OVERNIGHT: "10-hr rest",
  RESTART_34: "34-hr restart",
};

// Haversine distance in miles between two [lat, lng] points
function distanceMiles([lat1, lng1], [lat2, lng2]) {
  const R = 3958.8; // earth radius in miles
  const toRad = (deg) => (deg * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(a)));
}

export default function MapView({ trip }) {
  const routeLatLngs = useMemo(() => {
    if (!trip?.route_geometry) return [];
    return trip.route_geometry.map(([lng, lat]) => [lat, lng]);
  }, [trip]);

  const bounds = useMemo(() => {
    if (routeLatLngs.length === 0) return null;
    return routeLatLngs;
  }, [routeLatLngs]);

  const cumulativeDistances = useMemo(() => {
    if (routeLatLngs.length === 0) return [];
    const cum = [0];
    for (let i = 1; i < routeLatLngs.length; i++) {
      cum.push(
        cum[i - 1] + distanceMiles(routeLatLngs[i - 1], routeLatLngs[i]),
      );
    }
    return cum;
  }, [routeLatLngs]);

  const totalRouteDistance =
    cumulativeDistances[cumulativeDistances.length - 1] || 1;

  function indexForDistance(targetMiles) {
    if (cumulativeDistances.length === 0) return 0;
    let lo = 0;
    let hi = cumulativeDistances.length - 1;
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (cumulativeDistances[mid] < targetMiles) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  }

  const stopMarkers = useMemo(() => {
    if (!trip?.stops || routeLatLngs.length === 0) return [];
    return trip.stops.map((stop) => {
      const targetMiles =
        stop.distance_at_stop_miles != null ? stop.distance_at_stop_miles : 0;
      const idx = indexForDistance(Math.min(targetMiles, totalRouteDistance));
      return { ...stop, position: routeLatLngs[idx] };
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trip, routeLatLngs, cumulativeDistances, totalRouteDistance]);

  if (routeLatLngs.length === 0) return null;

  return (
    <div className="map-view">
      <MapContainer
        bounds={bounds}
        boundsOptions={{ padding: [40, 40] }}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution="&copy; OpenStreetMap contributors &copy; CARTO"
        />
        <Polyline
          positions={routeLatLngs}
          pathOptions={{ color: "#ffb627", weight: 4, opacity: 0.85 }}
        />

        {stopMarkers.map((stop, i) => (
          <CircleMarker
            key={i}
            center={stop.position}
            radius={7}
            pathOptions={{
              color: STOP_COLORS[stop.stop_type] || "#fff",
              fillColor: STOP_COLORS[stop.stop_type] || "#fff",
              fillOpacity: 0.9,
              weight: 2,
            }}
          >
            <Tooltip direction="top" offset={[0, -6]}>
              <strong>{STOP_LABELS[stop.stop_type] || stop.stop_type}</strong>
              <br />
              {stop.location_label} · hour {stop.trip_hour_start.toFixed(1)}
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>

      <div className="map-legend">
        {Object.entries(STOP_LABELS).map(([key, label]) => (
          <div className="map-legend__item" key={key}>
            <span
              className="map-legend__dot"
              style={{ background: STOP_COLORS[key] }}
            />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}
