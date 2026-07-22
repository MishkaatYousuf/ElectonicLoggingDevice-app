from rest_framework import serializers
from .models import Trip, Stop, LogSheet, DutySegment


class DutySegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutySegment
        fields = ["status", "start_hour", "end_hour", "note"]


class LogSheetSerializer(serializers.ModelSerializer):
    segments = DutySegmentSerializer(many=True, read_only=True)

    class Meta:
        model = LogSheet
        fields = [
            "day_index", "date_label", "total_driving_hours",
            "total_on_duty_hours", "total_off_duty_hours",
            "total_sleeper_hours", "segments",
        ]


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = [
            "stop_type", "sequence", "lat", "lng", "location_label",
            "trip_hour_start", "trip_hour_end", "duration_hours",
        ]


class TripInputSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    current_cycle_used_hours = serializers.FloatField(min_value=0, max_value=70)


class TripResultSerializer(serializers.ModelSerializer):
    stops = StopSerializer(many=True, read_only=True)
    log_sheets = LogSheetSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id", "current_location", "pickup_location", "dropoff_location",
            "current_location_lat", "current_location_lng",
            "pickup_location_lat", "pickup_location_lng",
            "dropoff_location_lat", "dropoff_location_lng",
            "current_cycle_used_hours", "total_distance_miles",
            "total_driving_hours", "route_geometry", "created_at",
            "stops", "log_sheets",
        ]
