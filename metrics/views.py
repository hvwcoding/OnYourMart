from django.contrib.auth.decorators import login_required
from django.db.models import Q, ExpressionWrapper, BooleanField
from django.shortcuts import render

from listing.models import Listing, Status
from order.models import Order
from .models import UserMetrics, CityMetrics, PlatformMetrics


def get_user_metrics(request):
    user_metrics = UserMetrics.objects.get(user=request.user)
    contribution_ratio = user_metrics.calculate_user_contribution_ratio()
    return {
        'user_active_listing': user_metrics.active_listing,
        'user_pending_listing': user_metrics.pending_listing,
        'user_settled_listing': user_metrics.settled_listing,
        'user_total_listing': user_metrics.total_listing(),
        'user_delivery_order': user_metrics.delivery_order,
        'user_meetup_order': user_metrics.meetup_order,
        'user_total_order': user_metrics.total_order(),
        'user_active_price': user_metrics.active_price,
        'user_pending_price': user_metrics.pending_price,
        'user_settled_price': user_metrics.settled_price,
        'user_total_price': user_metrics.total_price(),
        'user_delivery_weight': user_metrics.delivery_weight,
        'user_meetup_weight': user_metrics.meetup_weight,
        'user_total_weight': user_metrics.total_weight(),
        'user_contribution_ratio': contribution_ratio,
    }


def get_city_metrics(user_metrics):
    city_metrics = CityMetrics.objects.get(city=user_metrics.user.city)
    contribution_ratio = city_metrics.calculate_city_contribution_ratio()
    return {
        'city_contribution_ratio': contribution_ratio,
    }


def get_platform_metrics():
    platform_metrics = PlatformMetrics.objects.last()

    if platform_metrics is None:
        return {'error': 'No Platform Metrics available'}

    contribution_ratio = platform_metrics.calculate_platform_contribution_ratio()

    return {
        'platform_active_listing': platform_metrics.active_listing,
        'platform_pending_listing': platform_metrics.pending_listing,
        'platform_settled_listing': platform_metrics.settled_listing,
        'platform_total_listing': platform_metrics.total_listing,
        'platform_delivery_order': platform_metrics.delivery_order,
        'platform_meetup_order': platform_metrics.meetup_order,
        'platform_total_order': platform_metrics.total_order(),
        'platform_active_price': platform_metrics.active_price,
        'platform_pending_price': platform_metrics.pending_price,
        'platform_settled_price': platform_metrics.settled_price,
        'platform_total_price':
            platform_metrics.total_price() if platform_metrics.total_price() is not None else 0.0,
        'platform_delivery_weight': platform_metrics.delivery_weight,
        'platform_meetup_weight': platform_metrics.meetup_weight,
        'platform_total_weight': platform_metrics.total_weight(),
        'platform_contribution_ratio': contribution_ratio,
    }


@login_required
def kpi_user(request):
    user_metrics = get_user_metrics(request)
    city_metrics = get_city_metrics(UserMetrics.objects.get(user=request.user))

    # listing data
    all_listing = Listing.objects.filter(
        Q(user=request.user) |
        Q(order__buyer=request.user) |
        Q(order__seller=request.user)
    ).annotate(
        is_user_listing=ExpressionWrapper(
            Q(user=request.user),
            output_field=BooleanField()
        )
    ).distinct()

    active_listing = all_listing.filter(
        status=Status.objects.get(name='Active')
    )

    pending_listing = Order.objects.filter(
        Q(buyer=request.user) |
        Q(seller=request.user),
        listing__status=Status.objects.get(name='Pending')
    ).annotate(
        is_user_listing=ExpressionWrapper(
            Q(listing__user=request.user),
            output_field=BooleanField()
        )
    )

    settled_listing = Order.objects.filter(
        Q(buyer=request.user) |
        Q(seller=request.user),
        listing__status=Status.objects.get(name='Settled')
    ).annotate(
        is_user_listing=ExpressionWrapper(
            Q(listing__user=request.user),
            output_field=BooleanField()
        )
    )

    context = {
        **user_metrics,
        **city_metrics,
        'all_listing': all_listing,
        'active_listing': active_listing,
        'pending_listing': pending_listing,
        'settled_listing': settled_listing,
        'user_contribution_ratio': user_metrics['user_contribution_ratio'],
    }

    return render(request, 'kpi_user.html', context)


def kpi_overview(request):
    all_city_metrics = CityMetrics.objects.all()
    platform_metrics = get_platform_metrics()

    city_data = [
        {
            'name': city_metrics.city.name,
            'value': float(city_metrics.calculate_city_contribution_ratio()),
            'listing': city_metrics.total_listing,
            'order': city_metrics.total_order,
            'price': float(city_metrics.total_price),
            'total_weight': float(city_metrics.total_weight()),
            'delivery_weight': float(city_metrics.delivery_weight),
            'meetup_weight': float(city_metrics.meetup_weight),

        }
        for city_metrics in all_city_metrics
    ]

    city_data = sorted(city_data, key=lambda x: (-x['value'], x['name']))[:20]

    context = {
        'city_data': city_data,
        'platform_data': platform_metrics,
        'platform_contribution_ratio': platform_metrics['platform_contribution_ratio'],
    }

    return render(request, 'kpi_overview.html', context)
