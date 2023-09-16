import logging

from decimal import Decimal

from django.db import models

from user.models import CustomUser, City

logger = logging.getLogger('django')


class UserMetrics(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    active_listing = models.IntegerField(default=0)
    pending_listing = models.IntegerField(default=0)
    settled_listing = models.IntegerField(default=0)
    active_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    settled_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_order = models.IntegerField(default=0)
    meetup_order = models.IntegerField(default=0)
    delivery_weight = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    meetup_weight = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    contribution_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def total_listing(self):
        return self.active_listing + self.pending_listing + self.settled_listing

    def total_price(self):
        return self.active_price + self.pending_price + self.settled_price

    def total_order(self):
        return self.delivery_order + self.meetup_order

    def total_weight(self):
        return self.delivery_weight + self.meetup_weight

    def calculate_user_contribution_ratio(self):
        city_metrics = CityMetrics.objects.get(city=self.user.city)
        city_weight = Decimal(str(city_metrics.delivery_weight + city_metrics.meetup_weight))

        if not city_weight or city_weight == Decimal("0.00"):
            logger.warning("City weight for {} is zero!".format(self.user.city))
            return Decimal("0.00")

        ratio = (Decimal(str(self.delivery_weight + self.meetup_weight)) / city_weight) * Decimal("100")
        return max(Decimal("0.00"), min(ratio, Decimal("100.00")))

    def __str__(self):
        return self.user.email


class CityMetrics(models.Model):
    city = models.OneToOneField(City, on_delete=models.CASCADE)
    total_listing = models.IntegerField(default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_order = models.IntegerField(default=0)
    delivery_weight = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    meetup_weight = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    contribution_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def total_weight(self):
        return self.delivery_weight + self.meetup_weight

    def calculate_city_contribution_ratio(self):
        platform_metrics = PlatformMetrics.objects.last()
        platform_weight = Decimal(str(platform_metrics.delivery_weight + platform_metrics.meetup_weight))

        if not platform_weight or platform_weight == Decimal("0.00"):
            logger.warning("Platform weight is zero!")
            return Decimal("0.00")

        ratio = (Decimal(str(self.delivery_weight + self.meetup_weight)) / platform_weight) * Decimal("100")
        return max(Decimal("0.00"), min(ratio, Decimal("100.00")))

    def __str__(self):
        return self.city.name


class PlatformMetrics(models.Model):
    active_listing = models.IntegerField(default=0)
    pending_listing = models.IntegerField(default=0)
    settled_listing = models.IntegerField(default=0)
    active_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    settled_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_order = models.IntegerField(default=0)
    meetup_order = models.IntegerField(default=0)
    delivery_weight = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    meetup_weight = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    uk_waste = models.DecimalField(max_digits=20, decimal_places=2, default=22220000.00)
    contribution_ratio = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def total_listing(self):
        return self.active_listing + self.pending_listing + self.settled_listing

    def total_price(self):
        return self.active_price + self.pending_price + self.settled_price

    def total_order(self):
        return self.delivery_order + self.meetup_order

    def total_weight(self):
        return self.delivery_weight + self.meetup_weight

    # 222.2 million tonnes in kg (2018) = 222200000000 kg
    # x0.01% = 22220000 kg

    def calculate_platform_contribution_ratio(self):
        if self.uk_waste:
            print("Total Weight before conversion: ", self.delivery_weight + self.meetup_weight)

            total_weight = Decimal(self.delivery_weight + self.meetup_weight)
            uk_waste = Decimal(self.uk_waste)

            ratio = (total_weight / uk_waste) * Decimal("100")
            print("Calculated Ratio:", ratio)

            rounded_ratio = ratio.quantize(Decimal('0.00000000'))
            print("Rounded Ratio:", rounded_ratio)

            return max(Decimal("0.00"), min(rounded_ratio, Decimal("100.00")))
        else:
            logger.warning("UK weight is zero!")
            return Decimal("0.00")

    def __str__(self):
        return "Platform Metrics"
