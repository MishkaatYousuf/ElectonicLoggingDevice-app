import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip } from 'react-leaflet'
import { useMemo } from 'react'
import './MapView.css'

const STOP_COLORS = {
  PICKUP: '#34d399',
  DROPOFF: '#e5484d',
  FUEL: '#5b9dd9',
  REST_BREAK: '#ffb627',
  OVERNIGHT: '#a78bfa',
  RESTART_34: '#f472b6',
}

const STOP_LABELS = {
  PICKUP: 'Pickup',
  DROPOFF: 'Drop-off',
  FUEL: 'Fuel stop',
  REST_BREAK: '30-min break',
  OVERNIGHT: '10-hr rest',
  RESTART_34: '34-hr restart',
}

export default function MapView({ trip }) {
  const routeLatLngs = useMemo(() => {
    if (!trip?.route_geometry) return []
    // geometry is stored as [lng, lat] pairs (GeoJSON order)
    return trip.route_geometry.map(([lng, lat]) => [lat, lng])
  }, [trip])

  const bounds = useMemo(() => {
    if (routeLatLngs.length === 0) return null
    return routeLatLngs
  }, [routeLatLngs])

  const center = routeLatLngs[Math.floor(routeLatLngs.length / 2)] || [39.5, -98.35]

  // approximate stop positions along the route by fraction of trip hours
  const totalHours = trip?.stops?.length
    ? Math.max(...trip.stops.map((s) => s.trip_hour_end))
    : 1

  const stopMarkers = useMemo(() => {
    if (!trip?.stops || routeLatLngs.length === 0) return []
    return trip.stops.map((stop) => {
      const fraction = totalHours > 0 ? stop.trip_hour_start / totalHours : 0
      const idx = Math.min(
        routeLatLngs.length - 1,
        Math.max(0, Math.round(fraction * (routeLatLngs.length - 1)))
      )
      return { ...stop, position: routeLatLngs[idx] }
    })
  }, [trip, routeLatLngs, totalHours])

  if (routeLatLngs.length === 0) return null

  return (
    <div className="map-view">
      <MapContainer
        bounds={bounds}
        boundsOptions={{ padding: [40, 40] }}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap contributors &copy; CARTO'
        />
        <Polyline positions={routeLatLngs} pathOptions={{ color: '#ffb627', weight: 4, opacity: 0.85 }} />

        {stopMarkers.map((stop, i) => (
          <CircleMarker
            key={i}
            center={stop.position}
            radius={7}
            pathOptions={{
              color: STOP_COLORS[stop.stop_type] || '#fff',
              fillColor: STOP_COLORS[stop.stop_type] || '#fff',
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
            <span className="map-legend__dot" style={{ background: STOP_COLORS[key] }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  )
}
