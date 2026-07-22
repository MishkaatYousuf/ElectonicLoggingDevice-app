const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

export async function planTrip(payload) {
  const res = await fetch(`${API_BASE_URL}/trips/plan/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    let message = `Request failed (${res.status})`
    try {
      const body = await res.json()
      message = body.error || JSON.stringify(body)
    } catch (_) { /* ignore */ }
    throw new Error(message)
  }

  return res.json()
}
