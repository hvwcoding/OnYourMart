from django.contrib import admin

from .models import City, University, CustomUser

admin.site.register(City)
admin.site.register(University)
admin.site.register(CustomUser)