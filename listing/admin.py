from django.contrib import admin

from .models import Category, ListingType, Photo, Condition, MeetupPoint, Status, Listing

admin.site.register(Category)
admin.site.register(ListingType)
admin.site.register(Photo)
admin.site.register(Condition)
admin.site.register(MeetupPoint)
admin.site.register(Status)
admin.site.register(Listing)
