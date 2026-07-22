from django.urls import path
from .views import TripPlanView, TripDetailView, TripListView

urlpatterns = [
    path("trips/plan/", TripPlanView.as_view(), name="trip-plan"),
    path("trips/<int:pk>/", TripDetailView.as_view(), name="trip-detail"),
    path("trips/", TripListView.as_view(), name="trip-list"),
]
