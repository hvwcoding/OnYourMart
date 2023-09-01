from __future__ import absolute_import, unicode_literals

import logging

from celery import shared_task
from django.db.models.signals import post_save

from .models import Listing, Status, Order

logger = logging.getLogger(__name__)


@shared_task
def update_listing_status(listing_id):
    logger.info("Attempting to update listing status for listing ID {}".format(listing_id))

    try:
        listing = Listing.objects.get(pk=listing_id)
        if listing.status.name == 'Pending':
            listing.status = Status.objects.get(name="Settled")
            listing.save()

            order = Order.objects.get(listing=listing)
            post_save.send(sender=Order, instance=order, created=False)

            logger.info("Listing ID {} status updated to 'Settled'".format(listing_id))
            logger.info("Order ID {} status updated to 'Settled'".format(order.id))

        else:
            logger.warning('Listing with ID {} is not in "Pending" status.'.format(listing_id))
    except Listing.DoesNotExist:
        logger.warning('Listing with ID {} does not exist.'.format(listing_id))
    except Status.DoesNotExist:
        logger.warning('Status "Settled" does not exist.')
