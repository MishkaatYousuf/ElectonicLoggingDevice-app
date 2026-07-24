from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

from .models import Trip, Stop, LogSheet, DutySegment
from .serializers import TripInputSerializer, TripResultSerializer
from .services.geocode import geocode, GeocodeError
from .services.routing import get_route, RoutingError
from .services.hos_calculator import plan_hos, split_events_into_daily_logs


class TripPlanView(APIView):
    """
    POST /api/trips/plan/
    body: { current_location, pickup_location, dropoff_location, current_cycle_used_hours }

    Geocodes all three locations, computes a driving route (current -> pickup
    -> dropoff), runs the HOS simulation, persists everything, and returns
    the full trip with stops + daily log sheets.
    """

    def post(self, request):
        input_serializer = TripInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        try:
            cur_lat, cur_lng, cur_label = geocode(data["current_location"])
            pu_lat, pu_lng, pu_label = geocode(data["pickup_location"])
            do_lat, do_lng, do_label = geocode(data["dropoff_location"])
        except GeocodeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            route = get_route([(cur_lat, cur_lng), (pu_lat, pu_lng), (do_lat, do_lng)])
        except RoutingError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        pickup_leg_miles = route["leg_distances_miles"][0] if route["leg_distances_miles"] else 0.0

        hos_result = plan_hos(
            distance_miles=route["distance_miles"],
            driving_hours=route["duration_hours"],
            current_cycle_used=data["current_cycle_used_hours"],
            pickup_leg_miles=pickup_leg_miles,
        )
        daily_logs = split_events_into_daily_logs(hos_result["events"])

        # --- Persist ---
        trip = Trip.objects.create(
            current_location=cur_label,
            current_location_lat=cur_lat,
            current_location_lng=cur_lng,
            pickup_location=pu_label,
            pickup_location_lat=pu_lat,
            pickup_location_lng=pu_lng,
            dropoff_location=do_label,
            dropoff_location_lat=do_lat,
            dropoff_location_lng=do_lng,
            current_cycle_used_hours=data["current_cycle_used_hours"],
            total_distance_miles=round(route["distance_miles"], 1),
            total_driving_hours=round(route["duration_hours"], 2),
            route_geometry=route["geometry"],
        )

        for i, s in enumerate(hos_result["stops"]):
            Stop.objects.create(
                trip=trip,
                stop_type=s["stop_type"],
                sequence=i,
                trip_hour_start=round(s["start"], 2),
                trip_hour_end=round(s["end"], 2),
                duration_hours=round(s["end"] - s["start"], 2),
                location_label=f"~mile {round(s['distance_at_stop'])}",
                distance_at_stop_miles=round(s["distance_at_stop"], 2),
            )
        for day in daily_logs:
            log_sheet = LogSheet.objects.create(
                trip=trip,
                day_index=day["day_index"],
                date_label=f"Day {day['day_index']}",
                total_driving_hours=day["total_driving_hours"],
                total_on_duty_hours=day["total_on_duty_hours"],
                total_off_duty_hours=day["total_off_duty_hours"],
                total_sleeper_hours=day["total_sleeper_hours"],
            )
            for seg in day["segments"]:
                DutySegment.objects.create(
                    log_sheet=log_sheet,
                    status=seg["status"],
                    start_hour=seg["start_hour"],
                    end_hour=seg["end_hour"],
                    note=seg["label"],
                )

        result_serializer = TripResultSerializer(trip)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)


class TripDetailView(generics.RetrieveAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripResultSerializer


class TripListView(generics.ListAPIView):
    queryset = Trip.objects.all().order_by("-created_at")
    serializer_class = TripResultSerializer
