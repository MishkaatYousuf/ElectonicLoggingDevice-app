from django.db import models


class Trip(models.Model):
    """A planned trip submitted by a driver."""

    current_location = models.CharField(max_length=255)
    current_location_lat = models.FloatField(null=True, blank=True)
    current_location_lng = models.FloatField(null=True, blank=True)

    pickup_location = models.CharField(max_length=255)
    pickup_location_lat = models.FloatField(null=True, blank=True)
    pickup_location_lng = models.FloatField(null=True, blank=True)

    dropoff_location = models.CharField(max_length=255)
    dropoff_location_lat = models.FloatField(null=True, blank=True)
    dropoff_location_lng = models.FloatField(null=True, blank=True)

    current_cycle_used_hours = models.FloatField(
        help_text="Hours already used in the driver's 70hr/8-day cycle"
    )

    total_distance_miles = models.FloatField(null=True, blank=True)
    total_driving_hours = models.FloatField(null=True, blank=True)

    route_geometry = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip #{self.pk}: {self.pickup_location} -> {self.dropoff_location}"


class Stop(models.Model):
    """A stop along the route (fuel, rest break, pickup, dropoff, overnight)."""

    STOP_TYPES = [
        ("PICKUP", "Pickup"),
        ("DROPOFF", "Dropoff"),
        ("FUEL", "Fuel"),
        ("REST_BREAK", "30-min Rest Break"),
        ("OVERNIGHT", "10-hr Off Duty / Overnight"),
        ("RESTART_34", "34-hr Restart"),
    ]

    trip = models.ForeignKey(Trip, related_name="stops", on_delete=models.CASCADE)
    stop_type = models.CharField(max_length=20, choices=STOP_TYPES)
    sequence = models.PositiveIntegerField()
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    location_label = models.CharField(max_length=255, blank=True)
    distance_at_stop_miles = models.FloatField(null=True, blank=True, default=0.0)
    trip_hour_start = models.FloatField(help_text="Hours elapsed since trip start")
    trip_hour_end = models.FloatField(help_text="Hours elapsed since trip start")
    duration_hours = models.FloatField()

    class Meta:
        ordering = ["sequence"]

    def __str__(self):
        return f"{self.stop_type} @ hour {self.trip_hour_start:.1f}"


class LogSheet(models.Model):
    """One 24-hour ELD daily log sheet belonging to a trip."""

    trip = models.ForeignKey(Trip, related_name="log_sheets", on_delete=models.CASCADE)
    day_index = models.PositiveIntegerField(help_text="1 = first day of trip, 2 = second, ...")
    date_label = models.CharField(max_length=20, blank=True)
    total_driving_hours = models.FloatField(default=0)
    total_on_duty_hours = models.FloatField(default=0)
    total_off_duty_hours = models.FloatField(default=0)
    total_sleeper_hours = models.FloatField(default=0)

    class Meta:
        ordering = ["day_index"]

    def __str__(self):
        return f"LogSheet day {self.day_index} for Trip #{self.trip_id}"


class DutySegment(models.Model):
    """A single duty-status segment drawn on a daily log grid (0-24h)."""

    STATUS_CHOICES = [
        ("OFF", "Off Duty"),
        ("SB", "Sleeper Berth"),
        ("D", "Driving"),
        ("ON", "On Duty (Not Driving)"),
    ]

    log_sheet = models.ForeignKey("LogSheet", related_name="segments", on_delete=models.CASCADE)
    status = models.CharField(max_length=3, choices=STATUS_CHOICES)
    start_hour = models.FloatField(help_text="0-24, hour of day this segment starts")
    end_hour = models.FloatField(help_text="0-24, hour of day this segment ends")
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["start_hour"]

    def __str__(self):
        return f"{self.status} {self.start_hour:.2f}-{self.end_hour:.2f}"
