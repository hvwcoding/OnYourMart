from _decimal import Decimal

from django.db import models

from listing.models import Listing, Status
from user.models import CustomUser


class ShippingFeeWeight(models.Model):
    logistics_option = models.ForeignKey('LogisticsOption', on_delete=models.CASCADE)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    weight = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return '{}, Delivery Fee: {} for {} kg'.format(self.logistics_option, self.fee, self.weight)

    class Meta:
        ordering = ['logistics_option', 'fee', 'weight']


class LogisticsOption(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Order(models.Model):
    listing = models.OneToOneField(Listing, on_delete=models.SET_NULL, null=True)
    buyer = models.ForeignKey(CustomUser, related_name='buyer_orders', on_delete=models.CASCADE)
    seller = models.ForeignKey(CustomUser, related_name='seller_orders', on_delete=models.CASCADE)
    logistics_option = models.ForeignKey(LogisticsOption, on_delete=models.SET_NULL, null=True)
    shipping_fee_weight = models.ForeignKey(ShippingFeeWeight, on_delete=models.SET_NULL, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    buyer_confirmed = models.BooleanField(default=False)
    seller_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return 'Transaction {} between {} and {}'.format(self.id, self.buyer, self.seller)
