import './TripStats.css'

export default function TripStats({ trip }) {
  const stopCounts = (trip.stops || []).reduce((acc, s) => {
    acc[s.stop_type] = (acc[s.stop_type] || 0) + 1
    return acc
  }, {})

  const items = [
    { label: 'Total distance', value: `${trip.total_distance_miles.toLocaleString()} mi` },
    { label: 'Driving time', value: `${trip.total_driving_hours.toFixed(1)} hrs` },
    { label: 'Days on the road', value: `${trip.log_sheets.length}` },
    { label: 'Fuel stops', value: `${stopCounts.FUEL || 0}` },
    { label: 'Rest breaks', value: `${stopCounts.REST_BREAK || 0}` },
    { label: 'Overnight resets', value: `${(stopCounts.OVERNIGHT || 0) + (stopCounts.RESTART_34 || 0)}` },
  ]

  return (
    <div className="trip-stats">
      {items.map((item) => (
        <div className="trip-stats__item" key={item.label}>
          <div className="trip-stats__value">{item.value}</div>
          <div className="trip-stats__label">{item.label}</div>
        </div>
      ))}
    </div>
  )
}
