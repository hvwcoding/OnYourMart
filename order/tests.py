from django.db.models.signals import post_save, post_delete
from listing.models import Listing, Status
from metrics.signals import listing_changes, order_changes
from .models import Order, LogisticsOption, ShippingFeeWeight
from listing.base import BaseTest

TEST_EMAIL = 'test@uni.ac.uk'
TEST_PASSWORD = 'testpassword123'


class OrderBaseTestCase(BaseTest):

    def setUp(self):
        self.disconnect_signals()
        self.setup_users()
        self.setup_logistics_options()
        self.setup_common_data()
        self.listing = Listing.objects.create(
            user=self.user,
            listing_type=self.listing_type,
            name=self.name,
            description=self.description,
            category=self.category,
            condition=self.condition,
            price=self.price,
            meetup_point=self.meetup_point,
            status=self.active_status
        )
        self.listing.save()

    def disconnect_signals(self):
        post_save.disconnect(listing_changes, sender=Listing)
        post_delete.disconnect(listing_changes, sender=Listing)
        post_save.disconnect(order_changes, sender=Order)
        post_delete.disconnect(order_changes, sender=Order)

    def setup_logistics_options(self):
        self.logistics_option = LogisticsOption.objects.create(name="Test Delivery Option")
        self.shipping_fee_weight = ShippingFeeWeight.objects.create(
            logistics_option=self.logistics_option,
            fee=3,
            weight=5
        )

    def create_order(self):
        return Order.objects.create(
            listing=self.listing,
            seller=self.user,
            buyer=self.another_user,
            logistics_option=self.logistics_option,
            shipping_fee_weight=self.shipping_fee_weight,
            weight=5,
            total_price=100)

    def test_order_crud_operations(self):
        # CREATE
        order = self.create_order()
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.seller, self.user)
        self.assertEqual(order.buyer, self.another_user)

        # READ
        order_from_db = Order.objects.get(id=order.id)
        self.assertEqual(order_from_db.seller, self.user)
        self.assertEqual(order_from_db.buyer, self.another_user)

        # UPDATE
        order.buyer = self.user
        order.save()
        self.assertEqual(order.buyer, self.user)

        # DELETE
        order.delete()
        self.assertEqual(Order.objects.count(), 0)
        self.listing.refresh_from_db()  # Refresh the listing from the database
        self.assertEqual(self.listing.status, self.active_status)


class OrderBaseMetricsTestCase(BaseTest):

    def setUp(self):
        self.setup_users()
        self.setup_delivery_options()
        self.setup_common_data()
        self.connect_signals()
        self.listing = Listing.objects.create(
            user=self.user,
            listing_type=self.listing_type,
            name=self.name,
            description=self.description,
            category=self.category,
            condition=self.condition,
            price=self.price,
            meetup_point=self.meetup_point,
            status=self.active_status
        )
        self.listing.save()
        self.settled_status = Status.objects.create(name="Settled")

    def setup_delivery_options(self):
        self.logistics_option_delivery = LogisticsOption.objects.create(name="Delivery")
        self.logistics_option_meetup = LogisticsOption.objects.create(name="Meetup")
        self.shipping_fee_weight = ShippingFeeWeight.objects.create(
            logistics_option=self.logistics_option_delivery,
            fee=3,
            weight=5
        )

    def create_order(self, logistics_option_name):
        logistics_option = self.logistics_option_meetup if logistics_option_name == "Meetup" else self.logistics_option_delivery
        return Order.objects.create(
            listing=self.listing,
            seller=self.user,
            buyer=self.another_user,
            logistics_option=logistics_option,
            shipping_fee_weight=self.shipping_fee_weight,
            weight=2,
            total_price=100.0,
        )

    def connect_signals(self):
        post_save.connect(listing_changes, sender=Listing)
        post_delete.connect(listing_changes, sender=Listing)
        post_save.connect(order_changes, sender=Order)
        post_delete.connect(order_changes, sender=Order)

    def assert_user_metrics(self, metrics, delivery_order, meetup_order, delivery_weight, meetup_weight):
        """Assert the metrics values for a given entity."""
        self.assertEqual(metrics.delivery_order, delivery_order)
        self.assertEqual(metrics.meetup_order, meetup_order)
        self.assertEqual(metrics.delivery_weight, delivery_weight)
        self.assertEqual(metrics.meetup_weight, meetup_weight)

    def assert_city_metrics(self, metrics, total_order, delivery_weight, meetup_weight):
        """Assert the metrics values for a given entity."""
        self.assertEqual(metrics.total_order, total_order)
        self.assertEqual(metrics.delivery_weight, delivery_weight)
        self.assertEqual(metrics.meetup_weight, meetup_weight)

    def assert_platform_metrics(self, metrics, delivery_order, meetup_order, delivery_weight, meetup_weight):
        """Assert the metrics values for a given entity."""
        self.assertEqual(metrics.delivery_order, delivery_order)
        self.assertEqual(metrics.meetup_order, meetup_order)
        self.assertEqual(metrics.delivery_weight, delivery_weight)
        self.assertEqual(metrics.meetup_weight, meetup_weight)


class OrderMetricsCRUDTestCase(OrderBaseMetricsTestCase):
    def test_create_order_with_meetup_signal(self):
        self.refresh_metrics()

        order = self.create_order("Meetup")
        self.listing.status = self.settled_status
        order.seller_confirmed = True
        order.buyer_confirmed = True
        self.listing.save()
        order.save()

        self.refresh_metrics()

        expected_order_weight = order.weight

        self.assert_user_metrics(self.user_metrics, 0, 1, 0, expected_order_weight)
        self.assert_city_metrics(self.city_metrics, 1, 0, expected_order_weight)
        self.assert_platform_metrics(self.platform_metrics, 0, 1, 0, expected_order_weight)

    def test_create_order_with_delivery_signal(self):
        self.refresh_metrics()

        order = self.create_order("Delivery")
        self.listing.status = self.settled_status
        self.listing.save()
        order.save()

        self.refresh_metrics()

        expected_order_weight = order.weight

        self.assert_user_metrics(self.user_metrics, 1, 0, expected_order_weight, 0)
        self.assert_city_metrics(self.city_metrics, 1, expected_order_weight, 0)
        self.assert_platform_metrics(self.platform_metrics, 1, 0, expected_order_weight, 0)
