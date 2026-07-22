import { useState } from 'react'
import TripForm from './components/TripForm'
import MapView from './components/MapView'
import TripStats from './components/TripStats'
import LogSheetSVG from './components/LogSheetSVG'
import { planTrip } from './api'
import './App.css'

export default function App() {
  const [trip, setTrip] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(payload) {
    setLoading(true)
    setError(null)
    setTrip(null)
    try {
      const result = await planTrip(payload)
      setTrip(result)
    } catch (err) {
      setError(err.message || 'Something went wrong planning the trip.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__eyebrow">HOURS-OF-SERVICE ROUTE PLANNER</div>
        <h1 className="app__title">
          Plan the route. <span className="app__title-accent">Draw the logs.</span>
        </h1>
        <p className="app__subtitle">
          Enter a trip and get a driving route, required stops, and FMCSA-style daily
          log sheets — auto-filled for a 70&nbsp;hr/8&#8209;day property-carrying driver.
        </p>
      </header>

      <main className="app__main">
        <TripForm onSubmit={handleSubmit} loading={loading} />

        {error && <div className="app__error">⚠ {error}</div>}

        {trip && (
          <div className="app__results">
            <section className="app__section">
              <h2 className="app__section-title">Route overview</h2>
              <TripStats trip={trip} />
            </section>

            <section className="app__section">
              <h2 className="app__section-title">Map & stops</h2>
              <MapView trip={trip} />
            </section>

            <section className="app__section">
              <h2 className="app__section-title">
                Daily log sheets
                <span className="app__section-sub">
                  {trip.log_sheets.length} sheet{trip.log_sheets.length !== 1 ? 's' : ''} generated
                </span>
              </h2>
              <div className="app__logsheets">
                {trip.log_sheets.map((day) => (
                  <LogSheetSVG key={day.day_index} day={day} />
                ))}
              </div>
            </section>
          </div>
        )}
      </main>

      <footer className="app__footer">
        Routing via OSRM · Geocoding via OpenStreetMap Nominatim · Built with Django + React
      </footer>
    </div>
  )
}
