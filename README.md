# ELD Trip Planner

A full-stack app for property-carrying truck drivers: enter a trip (current
location, pickup, drop-off, and current 70hr/8-day cycle hours used) and get
back a driving route on a map, all required stops (fuel, breaks, rests), and
auto-drawn FMCSA-style daily log sheets.

**Stack:** Django + Django REST Framework (backend/API/DB) · React + Vite
(frontend) · Leaflet (map) · OSRM + OpenStreetMap Nominatim (free routing &
geocoding, no API keys needed).

---

## 1. How it works (flow)

```
User fills form (current, pickup, dropoff, cycle hrs used)
        │
        ▼
POST /api/trips/plan/  ────────────────────────────────────────┐
        │                                                       │
        ▼                                                       │
1. Geocode all 3 locations       (Nominatim, free)               │
2. Get driving route + distance  (OSRM, free)      backend/     │
3. Run HOS simulation engine     (trips/services/                │
   -> splits trip into duty      hos_calculator.py)              │
   segments obeying 11hr/14hr/                                   │
   30-min-break/70hr/8-day rules                                 │
4. Persist Trip, Stop,                                            │
   LogSheet, DutySegment rows   (trips/models.py)                 │
        │                                                       │
        ▼                                                       │
Response: route geometry, stop list, per-day log sheets ────────┘
        │
        ▼
Frontend renders:
  - Map with route + color-coded stop markers   (MapView.jsx)
  - Trip stats strip                            (TripStats.jsx)
  - One drawn ELD grid per day, amber duty line (LogSheetSVG.jsx)
```

The HOS engine (`backend/trips/services/hos_calculator.py`) is the core of
this project. It walks forward in simulated hours and applies, in order:

- 1 hr on-duty for pickup, 1 hr for drop-off
- Max **11 hrs driving** per duty day
- Max **14 hr on-duty window** per duty day
- Mandatory **30-min break** after 8 cumulative hours of driving
- **10 consecutive hours off duty** to start a new duty day
- **Fuel stop** (30 min, on-duty) every 1,000 miles
- **34-hour restart** once the 70-hr/8-day cycle is reached

The result is split at midnight boundaries into individual daily logs, each
containing duty-status segments (`OFF`, `SB`, `D`, `ON`) that the frontend
draws as a continuous step-line on a 24-hour grid — the same shape as a
paper ELD log.

---

## 2. Project structure

```
eld-app/
├── backend/                  Django project
│   ├── eld_backend/          settings, urls, wsgi
│   ├── trips/
│   │   ├── models.py         Trip, Stop, LogSheet, DutySegment
│   │   ├── serializers.py
│   │   ├── views.py          TripPlanView (main endpoint)
│   │   ├── urls.py
│   │   └── services/
│   │       ├── geocode.py    Nominatim geocoding
│   │       ├── routing.py    OSRM routing
│   │       └── hos_calculator.py   HOS rules engine
│   ├── requirements.txt
│   ├── render.yaml           Render.com deploy blueprint
│   └── Procfile
└── frontend/                 React + Vite app
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   └── components/
    │       ├── TripForm.jsx
    │       ├── MapView.jsx
    │       ├── LogSheetSVG.jsx    <- draws the ELD log grid
    │       └── TripStats.jsx
    └── vercel.json
```

---

## 3. Local setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

```bash
cp .env.example .env            # defaults are fine for local dev

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

Backend runs at `http://127.0.0.1:8000`. Try it:

```bash
curl -X POST http://127.0.0.1:8000/api/trips/plan/ \
  -H "Content-Type: application/json" \
  -d '{
        "current_location": "Chicago, IL",
        "pickup_location": "Indianapolis, IN",
        "dropoff_location": "Atlanta, GA",
        "current_cycle_used_hours": 15
      }'
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env            # VITE_API_BASE_URL=http://127.0.0.1:8000/api
npm run dev
```

Open `http://localhost:5173`, fill in the form, submit, and you should see the map + generated log sheets.

---

## 4. Deployment

Vercel doesn't run long-lived Django processes, so the cleanest split is:
**backend on Render** (free tier, easy Postgres + Django support) and
**frontend on Vercel**.

## 5. Assumptions implemented

- Property-carrying driver, 70 hrs / 8-day cycle, no adverse driving conditions
- Fuel stop at least every 1,000 miles (30 min, on-duty not driving)
- 1 hour on-duty for pickup, 1 hour for drop-off
- Trip is assumed to start at 06:00 on day 1 (a reasonable default; there's no "trip start time" field in the spec)
- Average driving speed is derived from the OSRM route (`distance / duration`) rather than a flat assumption, so it reflects real road conditions
