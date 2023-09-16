from django.contrib import admin

from .models import UserMetrics, CityMetrics, PlatformMetrics

admin.site.register(UserMetrics)
admin.site.register(CityMetrics)
admin.site.register(PlatformMetrics)
