from _decimal import Decimal

from django.db.models import Sum
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver

from listing.models import Listing, Status
from .models import UserMetrics, CityMetrics, PlatformMetrics
from order.models import Order


@receiver(post_save, sender=Listing)
@receiver(post_delete, sender=Listing)
def listing_changes(sender, instance, **kwargs):
    # Check if the signal was triggered by a delete operation
    if kwargs['signal'] == post_delete:
        print("A Listing object was deleted.")
    else:
        # Check if a new object is being created
        if kwargs.get('created', False):
            print("A new Listing object was created.")
        else:
            print("A Listing object was updated.")

    user_metrics, created = UserMetrics.objects.get_or_create(user=instance.user)

    user_metrics.active_listing = Listing.objects.filter(user=instance.user, status__name='Active').count()
    user_metrics.active_price = Listing.objects.filter(user=instance.user, status__name='Active').aggregate(
        Sum('price'))['price__sum'] or Decimal('0.00')
    user_metrics.pending_listing = Listing.objects.filter(user=instance.user, status__name='Pending').count()
    user_metrics.pending_price = Listing.objects.filter(user=instance.user, status__name='Pending').aggregate(
        Sum('price'))['price__sum'] or Decimal('0.00')
    user_metrics.settled_listing = Listing.objects.filter(user=instance.user, status__name='Settled').count()
    user_metrics.settled_price = Listing.objects.filter(user=instance.user, status__name='Settled').aggregate(
        Sum('price'))['price__sum'] or Decimal('0.00')

    user_metrics.save()


@receiver(post_save, sender=UserMetrics)
def update_city_metrics(sender, instance, **kwargs):
    if kwargs.get('created', False):
        print("A new UserMetrics object was created.")
    else:
        print("An existing UserMetrics object was updated.")
    city = instance.user.city
    city_metrics, created = CityMetrics.objects.get_or_create(city=city)

    # Updated total_listing and total_price
    city_metrics.total_listing = UserMetrics.objects.filter(user__city=city).aggregate(
        total_listing=Sum('active_listing') + Sum('pending_listing') + Sum('settled_listing')
    )['total_listing'] or 0
    city_metrics.total_price = UserMetrics.objects.filter(user__city=city).aggregate(
        total_price=Sum('active_price') + Sum('pending_price') + Sum('settled_price')
    )['total_price'] or 0

    city_metrics.total_order = Order.objects.filter(
        listing__user__city=city
    ).count()

    city_metrics.delivery_weight = Order.objects.filter(
        listing__user__city=city,
        logistics_option__name='Delivery'
    ).aggregate(
        delivery_weight=Sum('weight')
    )['delivery_weight'] or 0

    city_metrics.meetup_weight = Order.objects.filter(
        listing__user__city=city,
        logistics_option__name='Meetup'
    ).aggregate(
        meetup_weight=Sum('weight')
    )['meetup_weight'] or 0

    contribution_ratio = city_metrics.calculate_city_contribution_ratio()
    city_metrics.contribution_ratio = contribution_ratio
    city_metrics.save()


@receiver(post_save, sender=CityMetrics)
def update_platform_metrics(sender, instance, **kwargs):
    if kwargs.get('created', False):
        print("A new CityMetrics object was created.")
    else:
        print("An existing CityMetrics object was updated.")
    platform_metrics, created = PlatformMetrics.objects.get_or_create(pk=1)

    # Updated active_listing, pending_listing, settled_listing, active_price, pending_price, settled_price
    platform_metrics.active_listing = UserMetrics.objects.aggregate(
        active_listing=Sum('active_listing'))['active_listing'] or 0
    platform_metrics.pending_listing = UserMetrics.objects.aggregate(
        pending_listing=Sum('pending_listing'))['pending_listing'] or 0
    platform_metrics.settled_listing = UserMetrics.objects.aggregate(
        settled_listing=Sum('settled_listing'))['settled_listing'] or 0
    platform_metrics.active_price = UserMetrics.objects.aggregate(
        active_price=Sum('active_price'))['active_price'] or 0
    platform_metrics.pending_price = UserMetrics.objects.aggregate(
        pending_price=Sum('pending_price'))['pending_price'] or 0
    platform_metrics.settled_price = UserMetrics.objects.aggregate(
        settled_price=Sum('settled_price'))['settled_price'] or 0

    platform_metrics.delivery_order = Order.objects.filter(
        logistics_option__name='Delivery'
    ).count()

    platform_metrics.meetup_order = Order.objects.filter(
        logistics_option__name='Meetup'
    ).count()

    platform_metrics.delivery_weight = Order.objects.filter(
        logistics_option__name='Delivery'
    ).aggregate(
        delivery_weight=Sum('weight')
    )['delivery_weight'] or 0

    platform_metrics.meetup_weight = Order.objects.filter(
        logistics_option__name='Meetup'
    ).aggregate(
        meetup_weight=Sum('weight')
    )['meetup_weight'] or 0

    contribution_ratio = platform_metrics.calculate_platform_contribution_ratio()
    platform_metrics.platform_contribution_ratio = contribution_ratio
    platform_metrics.save()


@receiver(post_save, sender=Order)
@receiver(post_delete, sender=Order)
def order_changes(sender, instance, **kwargs):
    # Check if the signal was triggered by a delete operation
    if kwargs['signal'] == post_delete:
        print("An order object was deleted.")
    else:
        # Check if a new object is being created
        if kwargs.get('created', False):
            print("A new order object was created.")
        else:
            print("An order object was updated.")

    # Check if the order is settled by users
    if instance.logistics_option.name == 'Meetup' and not (instance.seller_confirmed and instance.buyer_confirmed):
        return

    print("Updating order metrics...")
    user_metrics, created = UserMetrics.objects.get_or_create(user=instance.listing.user)

    user_metrics.delivery_order = Order.objects.filter(listing__status__name='Settled',
                                                       logistics_option__name='Delivery',
                                                       listing__user=instance.listing.user).count()
    user_metrics.meetup_order = Order.objects.filter(listing__status__name='Settled',
                                                     logistics_option__name='Meetup',
                                                     listing__user=instance.listing.user).count()
    user_metrics.delivery_weight = Order.objects.filter(listing__status__name='Settled',
                                                        logistics_option__name='Delivery',
                                                        listing__user=instance.listing.user).aggregate(
        total_weight=Sum('weight')
    )['total_weight'] or 0
    user_metrics.meetup_weight = Order.objects.filter(listing__status__name='Settled',
                                                      logistics_option__name='Meetup',
                                                      listing__user=instance.listing.user).aggregate(
        total_weight=Sum('weight')
    )['total_weight'] or 0

    contribution_ratio = user_metrics.calculate_user_contribution_ratio()
    user_metrics.contribution_ratio = contribution_ratio
    user_metrics.save()


# if delete an order, change the status of associated listing, from settled to active
@receiver(pre_delete, sender=Order)
def revert_listing_status(sender, instance, **kwargs):
    print("Reverting listing status...")
    listing = instance.listing
    listing.status = Status.objects.get(name='Active')
    listing.save()
