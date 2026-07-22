import { useState } from 'react'
import './TripForm.css'

const initialState = {
  current_location: '',
  pickup_location: '',
  dropoff_location: '',
  current_cycle_used_hours: '',
}

export default function TripForm({ onSubmit, loading }) {
  const [form, setForm] = useState(initialState)

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit({
      current_location: form.current_location.trim(),
      pickup_location: form.pickup_location.trim(),
      dropoff_location: form.dropoff_location.trim(),
      current_cycle_used_hours: parseFloat(form.current_cycle_used_hours || 0),
    })
  }

  const isValid =
    form.current_location.trim() &&
    form.pickup_location.trim() &&
    form.dropoff_location.trim() &&
    form.current_cycle_used_hours !== '' &&
    !Number.isNaN(parseFloat(form.current_cycle_used_hours))

  return (
    <form className="trip-form" onSubmit={handleSubmit}>
      <div className="trip-form__grid">
        <label className="field">
          <span className="field__label">
            <span className="field__index">01</span> Current location
          </span>
          <input
            type="text"
            placeholder="e.g. Chicago, IL"
            value={form.current_location}
            onChange={(e) => update('current_location', e.target.value)}
            required
          />
        </label>

        <label className="field">
          <span className="field__label">
            <span className="field__index">02</span> Pickup location
          </span>
          <input
            type="text"
            placeholder="e.g. Indianapolis, IN"
            value={form.pickup_location}
            onChange={(e) => update('pickup_location', e.target.value)}
            required
          />
        </label>

        <label className="field">
          <span className="field__label">
            <span className="field__index">03</span> Drop-off location
          </span>
          <input
            type="text"
            placeholder="e.g. Atlanta, GA"
            value={form.dropoff_location}
            onChange={(e) => update('dropoff_location', e.target.value)}
            required
          />
        </label>

        <label className="field">
          <span className="field__label">
            <span className="field__index">04</span> Cycle hours used (70hr/8day)
          </span>
          <input
            type="number"
            min="0"
            max="70"
            step="0.5"
            placeholder="e.g. 12"
            value={form.current_cycle_used_hours}
            onChange={(e) => update('current_cycle_used_hours', e.target.value)}
            required
          />
        </label>
      </div>

      <button type="submit" className="trip-form__submit" disabled={!isValid || loading}>
        {loading ? 'Calculating route & logs…' : 'Plan trip'}
      </button>
    </form>
  )
}
