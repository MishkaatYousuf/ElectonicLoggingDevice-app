"""
Hours-of-Service (HOS) simulation engine.

Assumptions (as given in the assignment):
- Property-carrying driver, 70 hrs / 8-day cycle
- No adverse driving conditions
- Fueling at least once every 1,000 miles
- 1 hour each for pickup and drop-off

Rules modeled (simplified, standard FMCSA property-carrying rules):
- 11-hour driving limit per duty day (after 10 consecutive hrs off duty)
- 14-hour on-duty window per duty day (driving not allowed after 14th hour
  since coming on duty)
- 30-minute break required after 8 cumulative hours of driving
- 70-hour / 8-day cycle limit -> triggers a 34-hour restart
- Trip is assumed to start at 06:00 on Day 1 (a reasonable default start time)

The simulation walks forward in simulated hours, producing a flat list of
"events" (duty-status segments) with absolute start/end hours from trip
start. These are later split at 24-hour (midnight) boundaries into daily
log sheets.
"""

FUEL_STOP_INTERVAL_MILES = 1000
FUEL_STOP_DURATION_HOURS = 0.5
PICKUP_DURATION_HOURS = 1.0
DROPOFF_DURATION_HOURS = 1.0
MAX_DRIVE_PER_DAY = 11.0
MAX_WINDOW_PER_DAY = 14.0
MAX_DRIVE_BEFORE_BREAK = 8.0
REQUIRED_BREAK_HOURS = 0.5
REQUIRED_OFF_DUTY_HOURS = 10.0
CYCLE_LIMIT_HOURS = 70.0
RESTART_HOURS = 34.0
TRIP_START_CLOCK_HOUR = 6.0  # trip assumed to begin at 6:00 AM

def plan_hos(distance_miles: float, driving_hours: float, current_cycle_used: float,
             pickup_leg_miles: float = 0.0):
    """
    Simulate the whole trip and return:
      - events: list of {status, start, end, label} in absolute trip hours
      - stops: list of {stop_type, start, end, distance_at_stop}
      - total_trip_hours

    pickup_leg_miles: distance (miles) from the driver's *current* location to
    the *pickup* location. The driver must physically drive this leg before
    the on-duty "Pickup" event is logged - it is not assumed to happen at
    mile 0.
    """
    events = []
    stops = []

    t = 0.0  # absolute hours since trip start
    cycle_used = current_cycle_used

    def add_event(status, start, end, label=""):
        if end > start:
            events.append({"status": status, "start": start, "end": end, "label": label})

    remaining_drive = driving_hours
    distance_covered = 0.0
    miles_per_hour = (distance_miles / driving_hours) if driving_hours > 0 else 50.0
    next_fuel_mark = FUEL_STOP_INTERVAL_MILES
    pickup_visited = False

    window_start = t
    drive_today = 0.0
    drive_since_break = 0.0

    def log_pickup():
        nonlocal t, cycle_used, pickup_visited
        add_event("ON", t, t + PICKUP_DURATION_HOURS, "Pickup")
        stops.append({
            "stop_type": "PICKUP", "start": t, "end": t + PICKUP_DURATION_HOURS,
            "distance_at_stop": distance_covered,
        })
        t += PICKUP_DURATION_HOURS
        cycle_used += PICKUP_DURATION_HOURS
        pickup_visited = True

    # Edge case: pickup location is effectively the same as current location
    if pickup_leg_miles <= 1e-6:
        log_pickup()

    safety_counter = 0
    while remaining_drive > 1e-6:
        safety_counter += 1
        if safety_counter > 2000:
            break  # safety valve against infinite loops

        window_elapsed = t - window_start
        window_remaining = MAX_WINDOW_PER_DAY - window_elapsed
        drive_cap_remaining = MAX_DRIVE_PER_DAY - drive_today
        break_cap_remaining = MAX_DRIVE_BEFORE_BREAK - drive_since_break
        miles_to_next_fuel = next_fuel_mark - distance_covered
        hours_to_next_fuel = miles_to_next_fuel / miles_per_hour if miles_per_hour > 0 else remaining_drive

        if not pickup_visited:
            miles_to_pickup = pickup_leg_miles - distance_covered
            hours_to_pickup = miles_to_pickup / miles_per_hour if miles_per_hour > 0 else remaining_drive
        else:
            hours_to_pickup = remaining_drive  # no constraint

        chunk = min(
            remaining_drive,
            window_remaining,
            drive_cap_remaining,
            break_cap_remaining,
            hours_to_next_fuel,
            hours_to_pickup,
        )

        if chunk <= 1e-6:
            # Need a break or a daily reset before continuing to drive
            if break_cap_remaining <= 1e-6:
                add_event("ON", t, t + REQUIRED_BREAK_HOURS, "30-min rest break")
                stops.append({
                    "stop_type": "REST_BREAK", "start": t, "end": t + REQUIRED_BREAK_HOURS,
                    "distance_at_stop": distance_covered,
                })
                t += REQUIRED_BREAK_HOURS
                cycle_used += REQUIRED_BREAK_HOURS
                drive_since_break = 0.0
                continue
            else:
                # 11-hr or 14-hr window exhausted -> 10 hr off duty reset
                add_event("OFF", t, t + REQUIRED_OFF_DUTY_HOURS, "10-hr off duty (daily reset)")
                stops.append({
                    "stop_type": "OVERNIGHT", "start": t, "end": t + REQUIRED_OFF_DUTY_HOURS,
                    "distance_at_stop": distance_covered,
                })
                t += REQUIRED_OFF_DUTY_HOURS
                window_start = t
                drive_today = 0.0
                drive_since_break = 0.0
                continue

        # Drive the chunk
        add_event("D", t, t + chunk, "Driving")
        t += chunk
        remaining_drive -= chunk
        drive_today += chunk
        drive_since_break += chunk
        cycle_used += chunk
        distance_covered += chunk * miles_per_hour

        # Arrived at pickup?
        if not pickup_visited and distance_covered >= pickup_leg_miles - 1e-6:
            log_pickup()

        # Fuel stop check
        if distance_covered >= next_fuel_mark - 1e-6 and remaining_drive > 1e-6:
            add_event("ON", t, t + FUEL_STOP_DURATION_HOURS, "Fuel stop")
            stops.append({
                "stop_type": "FUEL", "start": t, "end": t + FUEL_STOP_DURATION_HOURS,
                "distance_at_stop": distance_covered,
            })
            t += FUEL_STOP_DURATION_HOURS
            cycle_used += FUEL_STOP_DURATION_HOURS
            next_fuel_mark += FUEL_STOP_INTERVAL_MILES

        # 70-hr / 8-day cycle check -> 34-hr restart
        if cycle_used >= CYCLE_LIMIT_HOURS and remaining_drive > 1e-6:
            add_event("OFF", t, t + RESTART_HOURS, "34-hr restart (70-hr cycle reached)")
            stops.append({
                "stop_type": "RESTART_34", "start": t, "end": t + RESTART_HOURS,
                "distance_at_stop": distance_covered,
            })
            t += RESTART_HOURS
            cycle_used = 0.0
            window_start = t
            drive_today = 0.0
            drive_since_break = 0.0

    # Safety net: if driving_hours was 0 or extremely short and we never hit
    # the mid-loop check above, make sure pickup still gets logged.
    if not pickup_visited:
        log_pickup()

    # --- Dropoff (on duty, not driving) ---
    add_event("ON", t, t + DROPOFF_DURATION_HOURS, "Drop-off")
    stops.append({
        "stop_type": "DROPOFF", "start": t, "end": t + DROPOFF_DURATION_HOURS,
        "distance_at_stop": distance_covered,
    })
    t += DROPOFF_DURATION_HOURS

    return {
        "events": events,
        "stops": stops,
        "total_trip_hours": t,
    }

def split_events_into_daily_logs(events, trip_start_clock_hour=TRIP_START_CLOCK_HOUR):
    """
    Convert absolute-trip-hour events into a list of per-day logs, each
    containing segments clipped to that day's 0-24h window (matching the
    paper ELD grid, where hour 0 = midnight).
    """
    days = {}

    for ev in events:
        # Shift so hour 0 = midnight of day 1
        abs_start = ev["start"] + trip_start_clock_hour
        abs_end = ev["end"] + trip_start_clock_hour

        cursor = abs_start
        while cursor < abs_end - 1e-9:
            day_index = int(cursor // 24) + 1
            day_boundary = day_index * 24
            seg_end = min(abs_end, day_boundary)

            hour_in_day_start = cursor - (day_index - 1) * 24
            hour_in_day_end = seg_end - (day_index - 1) * 24

            days.setdefault(day_index, []).append({
                "status": ev["status"],
                "start_hour": round(hour_in_day_start, 3),
                "end_hour": round(hour_in_day_end, 3),
                "label": ev["label"],
            })

            cursor = seg_end

    # Build ordered list with totals
    result = []
    for day_index in sorted(days.keys()):
        segments = days[day_index]
        totals = {"D": 0.0, "ON": 0.0, "OFF": 0.0, "SB": 0.0}
        for seg in segments:
            totals[seg["status"]] += seg["end_hour"] - seg["start_hour"]

        result.append({
            "day_index": day_index,
            "segments": segments,
            "total_driving_hours": round(totals["D"], 2),
            "total_on_duty_hours": round(totals["ON"], 2),
            "total_off_duty_hours": round(totals["OFF"], 2),
            "total_sleeper_hours": round(totals["SB"], 2),
        })

    return result
