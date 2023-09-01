from django.contrib import admin

from .models import Order, LogisticsOption, ShippingFeeWeight

admin.site.register(Order)
admin.site.register(LogisticsOption)
admin.site.register(ShippingFeeWeight)
