from django.contrib import admin
from .models import Trip, Stop, LogSheet, DutySegment

admin.site.register(Trip)
admin.site.register(Stop)
admin.site.register(LogSheet)
admin.site.register(DutySegment)
