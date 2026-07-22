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
the assignment. It walks forward in simulated hours and applies, in order:

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

> `requirements.txt` is deliberately Postgres-free so it installs cleanly on
> every OS (including Windows, where `psycopg2-binary` sometimes fails to
> build). Local dev uses SQLite by default. The Postgres driver is only
> needed in production and lives in `requirements-prod.txt`, which Render
> installs automatically — you don't need to touch it locally.

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

Open `http://localhost:5173`, fill in the form, submit, and you should see
the map + generated log sheets.

---

## 4. Pushing to GitHub

```bash
cd eld-app
git init
git add .
git commit -m "Full-stack ELD trip planner: Django + React"
git branch -M main
git remote add origin https://github.com/<your-username>/eld-trip-planner.git
git push -u origin main
```

(The provided `.gitignore` already excludes `venv/`, `node_modules/`,
`db.sqlite3`, and `.env` files.)

---

## 5. Deployment

Vercel doesn't run long-lived Django processes, so the cleanest split is:
**backend on Render** (free tier, easy Postgres + Django support) and
**frontend on Vercel** (as the assignment asks). Railway or Fly.io work
identically to Render if you prefer.

### 5a. Backend → Render

1. Push the repo to GitHub (above).
2. Go to [render.com](https://render.com) → **New +** → **Blueprint**, and
   point it at your repo. Render will read `backend/render.yaml`
   automatically and provision a free Postgres DB + a web service.
   - If you'd rather set it up manually instead of via blueprint: **New +**
     → **Web Service** → connect your repo → set **Root Directory** to
     `backend` → **Build Command**:
     `pip install -r requirements-prod.txt && python manage.py collectstatic --noinput`
     → **Start Command**: `gunicorn eld_backend.wsgi:application --bind 0.0.0.0:$PORT`
3. Add environment variables (Render dashboard → Environment):
   - `SECRET_KEY` → any random string
   - `DEBUG` → `False`
   - `ALLOWED_HOSTS` → `*` (or your exact Render domain)
   - `CORS_ALLOW_ALL` → `True` (or set `CORS_ALLOWED_ORIGINS` to your Vercel URL)
   - `DATABASE_URL` → auto-filled if you attached the Render Postgres DB
4. After first deploy, open the Render **Shell** tab and run:
   `python manage.py migrate`
5. Note your live API URL, e.g. `https://eld-trip-planner-api.onrender.com`.

### 5b. Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New** → **Project** →
   import the same GitHub repo.
2. Set **Root Directory** to `frontend`.
3. Framework preset: **Vite** (auto-detected). Build command `npm run build`,
   output directory `dist` (already set in `frontend/vercel.json`).
4. Add an environment variable:
   - `VITE_API_BASE_URL` → `https://eld-trip-planner-api.onrender.com/api`
     (your Render URL from step 5a, with `/api` appended)
5. Deploy. Vercel gives you a live URL like
   `https://eld-trip-planner.vercel.app` — that's your hosted deliverable.
6. Go back to Render and set `CORS_ALLOWED_ORIGINS` to that exact Vercel URL
   (and set `CORS_ALLOW_ALL=False`) for a tighter production config.

> Free-tier note: Render's free web services spin down after inactivity, so
> the first request after idling can take ~30–50 seconds to wake up. That's
> expected — worth mentioning in your Loom so reviewers aren't confused by a
> slow first request.

---

## 6. Recording the Loom (3–5 min suggested outline)

1. **(30s)** Show the live Vercel URL, explain the objective in one sentence.
2. **(60s)** Fill out the form with a real multi-day trip (e.g. Chicago →
   Dallas → Miami with 20 cycle hours used) so more than one log sheet gets
   generated, submit it.
3. **(60s)** Walk the map: route line, colored stop markers, legend.
4. **(60s)** Walk a log sheet: point out the duty-status rows, the drawn
   line, totals pills, and that multiple sheets appear for multi-day trips.
5. **(60–90s)** Quick code tour: `hos_calculator.py` (the rules engine),
   `views.py` (`TripPlanView`), `models.py` (DB schema), and
   `LogSheetSVG.jsx` (how the grid is drawn).

---

## 7. Assumptions implemented

- Property-carrying driver, 70 hrs / 8-day cycle, no adverse driving conditions
- Fuel stop at least every 1,000 miles (30 min, on-duty not driving)
- 1 hour on-duty for pickup, 1 hour for drop-off
- Trip is assumed to start at 06:00 on day 1 (a reasonable default; there's
  no "trip start time" field in the spec)
- Average driving speed is derived from the OSRM route (`distance / duration`)
  rather than a flat assumption, so it reflects real road conditions

## 8. Possible follow-ups (mention if asked, don't need to build)

- Editable/draggable log segments for manual correction
- PDF export of log sheets
- Multi-stop trips (more than one pickup/drop-off)
- Real-time traffic-aware routing (would need a paid API like Mapbox or Google)
