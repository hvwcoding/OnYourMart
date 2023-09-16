import random
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.utils import timezone

from listing.models import Status
from .forms import CheckoutForm
from .models import Listing, ShippingFeeWeight
from .models import Order
from .tasks import update_listing_status


@login_required
def create_order(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    if request.user == listing.user:
        messages.error(request, 'You cannot purchase your own listing.')
        return redirect('listing_details', pk=listing.id)

    # Check if a ShippingFeeWeight object's ID is already stored in the session
    shipping_fee_weight_id = request.session.get('shipping_fee_weight_id')

    if not shipping_fee_weight_id:
        # Choose a ShippingFeeWeight object randomly for 'Delivery' option
        selected_shipping_fee_weight = random.choice(
            ShippingFeeWeight.objects.filter(logistics_option__name='Delivery'))
        request.session['shipping_fee_weight_id'] = selected_shipping_fee_weight.id
    else:
        selected_shipping_fee_weight = ShippingFeeWeight.objects.get(id=shipping_fee_weight_id)

    # Initialize delivery_fee to 0 for 'Meetup' option
    delivery_fee = Decimal(0.00)

    # If selected_shipping_fee_weight exists, then update delivery_fee
    if selected_shipping_fee_weight:
        delivery_fee = selected_shipping_fee_weight.fee

    # Calculate total_price regardless of whether it is a POST or GET request
    total_price = listing.price + delivery_fee

    if request.method == 'POST':
        form = CheckoutForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)
            order.listing = listing
            order.buyer = request.user
            order.seller = listing.user
            logistics_option = form.cleaned_data['logistics_option']

            if logistics_option.name == 'Meetup':
                order.weight = random.choice(
                    ShippingFeeWeight.objects.filter(logistics_option__name='Meetup')).weight
                order.total_price = listing.price
            elif logistics_option.name == 'Delivery':
                order.shipping_fee_weight = selected_shipping_fee_weight
                order.weight = selected_shipping_fee_weight.weight
                order.total_price = listing.price + selected_shipping_fee_weight.fee
                update_listing_status.apply_async((listing.id,), countdown=60)

            # Update the listing's status
            listing.status = Status.objects.get(name='Pending')
            listing.save()
            order.save()

            messages.success(request, 'Purchase successful! Order ID: ' + str(order.id))
            return redirect('purchase_confirmation', order_id=order.id)
    else:
        form = CheckoutForm()

        # Calculate the total price
        if selected_shipping_fee_weight:
            delivery_fee = selected_shipping_fee_weight.fee

    total_price = listing.price + delivery_fee

    return render(request, 'checkout.html', {
        'form': form,
        'listing': listing,
        'delivery_fee': delivery_fee,
        'total_price': total_price,
    })


def received_order(request, order_id):
    order = Order.objects.get(pk=order_id)
    return render(request, 'purchase_confirmation.html', {'order': order})


def mark_order(request, order_id, role):
    order = get_object_or_404(Order, id=order_id)
    other_party = None

    # Ensure the role is either 'seller' or 'buyer'
    if role == 'seller':
        order.seller_confirmed = True
        other_party = 'buyer'
    elif role == 'buyer':
        order.buyer_confirmed = True
        other_party = 'seller'
    else:
        messages.error(request, 'Invalid role specified.')
        return redirect('listing_details', pk=order.listing.id)

    # Check if both parties have confirmed the order
    if order.buyer_confirmed and order.seller_confirmed:
        order.listing.status = Status.objects.get(name='Settled')
        order.listing.save()
        order.completed_date = timezone.now()
        message = 'Thank you for your confirmation, the status has been marked as settled.'
    else:
        message = 'Thank you for your confirmation, please wait for the other party ({}) for double confirmation.'.format(
            other_party)

    order.save()
    messages.success(request, message)

    return redirect('listing_details', pk=order.listing.id)


@receiver(post_save, sender=Order)
def update_completed_date(sender, instance, **kwargs):
    if instance.listing.status.name == 'Settled' and not instance.completed_date:
        instance.completed_date = timezone.now()
        instance.save()

