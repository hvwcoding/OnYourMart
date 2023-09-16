from functools import wraps

from django.db.models.signals import post_save, post_delete

from metrics.signals import listing_changes
from .models import CustomUser, Listing, ListingType, Category, Condition, MeetupPoint, Status
from .base import BaseTest

import threading

# Constants:
TEST_EMAIL = 'test@uni.ac.uk'
TEST_PASSWORD = 'testpassword123'


class ListingBaseTestCase(BaseTest):

    def setUp(self):
        """Set up common test data"""
        # Disconnect the post_save signal handler temporarily
        self.disconnect_signals()
        self.user = CustomUser.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        self.setup_common_data()
        self.setup_listing_data()

    def setup_listing_data(self):
        self.listing = Listing.objects.create(
            user=self.user,
            listing_type=self.listing_type,
            name=self.name,
            description=self.description,
            category=self.category,
            condition=self.condition,
            price=self.price,
            meetup_point=self.meetup_point,
            status=self.active_status,
        )
        self.listing.save()

    def disconnect_signals(self):
        post_save.disconnect(listing_changes, sender=Listing)
        post_delete.disconnect(listing_changes, sender=Listing)


def manage_signals(model, signal_handler):
    """Decorator to disconnect and reconnect signals before and after the function."""

    @wraps(model)
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Disconnect
            post_save.disconnect(signal_handler, sender=model)
            post_delete.disconnect(signal_handler, sender=model)

            result = func(*args, **kwargs)

            # Reconnect
            post_save.connect(signal_handler, sender=model)
            post_delete.connect(signal_handler, sender=model)

            return result

        return wrapper

    return decorator


class ModelCRUDMixin:
    """Mixin to handle CRUD operations for a given model."""

    model = None
    test_name = ""
    instance = None
    signal_handler = None

    @manage_signals(model=Listing, signal_handler=listing_changes)
    def test_create(self):
        instance = self.model.objects.create(name=f"New {self.test_name}")
        self.assertEqual(instance.name, f"New {self.test_name}")

    @manage_signals(model=Listing, signal_handler=listing_changes)
    def test_read(self):
        instance = self.model.objects.get(pk=self.instance.pk)
        self.assertEqual(instance.name, self.instance.name)

    @manage_signals(model=Listing, signal_handler=listing_changes)
    def test_update(self):
        self.instance.name = f"Updated {self.test_name}"
        self.instance.save()
        updated_instance = self.model.objects.get(pk=self.instance.pk)
        self.assertEqual(updated_instance.name, f"Updated {self.test_name}")

    @manage_signals(model=Listing, signal_handler=listing_changes)
    def test_delete(self):
        self.instance.delete()
        with self.assertRaises(self.model.DoesNotExist):
            self.model.objects.get(pk=self.instance.pk)


class CategoryTestCase(ListingBaseTestCase, ModelCRUDMixin):
    model = Category
    test_name = "Category"
    instance = None

    def setUp(self):
        super().setUp()
        self.instance = self.category


class ListingTypeTestCase(ListingBaseTestCase, ModelCRUDMixin):
    model = ListingType
    test_name = "Listing Type"
    instance = None

    def setUp(self):
        super().setUp()
        self.instance = self.listing_type


class ConditionTestCase(ListingBaseTestCase, ModelCRUDMixin):
    model = Condition
    test_name = "Condition"
    instance = None

    def setUp(self):
        super().setUp()
        self.instance = self.condition


class MeetupPointTestCase(ListingBaseTestCase, ModelCRUDMixin):
    model = MeetupPoint
    test_name = "Meetup Point"
    instance = None

    def setUp(self):
        super().setUp()
        self.instance = self.meetup_point


class StatusTestCase(ListingBaseTestCase, ModelCRUDMixin):
    model = Status
    test_name = "Status"
    instance = None

    def setUp(self):
        super().setUp()
        self.instance = self.active_status


class ListingTestCase(ListingBaseTestCase, ModelCRUDMixin):
    model = Listing
    test_name = "Listing"
    instance = None

    def setUp(self):
        super().setUp()
        self.instance = self.listing

    @manage_signals(model=Listing, signal_handler=listing_changes)
    def test_create(self):
        instance = self.model.objects.create(
            user=self.user,
            listing_type=self.listing_type,
            name=f"New {self.test_name}",
            description=self.description,
            category=self.category,
            condition=self.condition,
            price=self.price,
            meetup_point=self.meetup_point,
            status=self.active_status,
        )
        self.assertEqual(instance.name, f"New {self.test_name}")


class ListingBaseMetricsTestCase(BaseTest):
    def setUp(self):
        """Set up common test data"""
        self.setup_users()
        self.setup_common_data()
        self.setup_listing_data(self.user)
        self.setup_listing_data(self.another_user)

    def setup_listing_data(self, user):
        """Initialize listing data for a specific user.
        Args:
            user: The user entity for whom the listing data is to be set up.
        """

        self.pending_status = Status.objects.create(name="Pending")
        self.settled_status = Status.objects.create(name="Settled")

        self.listing = Listing.objects.create(
            user=user,
            listing_type=self.listing_type,
            name=self.name,
            description=self.description,
            category=self.category,
            condition=self.condition,
            price=self.price,
            meetup_point=self.meetup_point,
            status=self.active_status
        )

    def update_listing(self, user, price=None, status=None, **kwargs):
        """Update listing details for a specific user."""

        listing = Listing.objects.get(user=user)

        if price is not None:
            listing.price = price

        if status is not None:
            listing.status = status

        for key, value in kwargs.items():
            setattr(listing, key, value)

        listing.save()

    def assert_user_metrics(self, metrics, active_listing, active_price,
                            pending_listing=0, pending_price=0, settled_listing=0, settled_price=0):
        """Assert the metrics values for a UserMetrics entity."""
        self.assertEqual(metrics.active_listing, active_listing)
        self.assertEqual(metrics.active_price, active_price)
        self.assertEqual(metrics.pending_listing, pending_listing)
        self.assertEqual(metrics.pending_price, pending_price)
        self.assertEqual(metrics.settled_listing, settled_listing)
        self.assertEqual(metrics.settled_price, settled_price)

    def assert_city_metrics(self, metrics, total_listing, total_price):
        """Assert the metrics values for a CityMetrics entity."""
        self.assertEqual(metrics.total_listing, total_listing)
        self.assertEqual(metrics.total_price, total_price)

    def assert_platform_metrics(self, metrics, active_listing, active_price,
                            pending_listing=0, pending_price=0, settled_listing=0, settled_price=0):
        """Assert the metrics values for a PlatformMetrics entity."""
        self.assertEqual(metrics.active_listing, active_listing)
        self.assertEqual(metrics.active_price, active_price)
        self.assertEqual(metrics.pending_listing, pending_listing)
        self.assertEqual(metrics.pending_price, pending_price)
        self.assertEqual(metrics.settled_listing, settled_listing)
        self.assertEqual(metrics.settled_price, settled_price)


class ListingMetricsCRUDTestCase(ListingBaseMetricsTestCase):
    """Test case for the listing_changes signal handler."""

    def test_current_listings(self):
        """Assert the current metrics values."""
        self.refresh_metrics()

        self.assert_user_metrics(self.user_metrics, 1, 50)
        self.assert_city_metrics(self.city_metrics, 1, 50)
        self.assert_user_metrics(self.another_user_metrics, 1,  50)
        self.assert_city_metrics(self.another_city_metrics, 1,  50)
        self.assert_platform_metrics(self.platform_metrics, 2, 100)

    def test_create_listing_updates_metrics_for_single_user(self):
        """Test that creating a listing for the first user updates the metrics."""
        new_listing = Listing.objects.create(
            user=self.user,
            listing_type=self.listing_type,
            name=self.name,
            description=self.description,
            category=self.category,
            condition=self.condition,
            price=100,
            meetup_point=self.meetup_point,
            status=self.active_status
        )

        self.refresh_metrics()

        self.assert_user_metrics(self.user_metrics, 2, 150)
        self.assert_city_metrics(self.city_metrics, 2, 150)
        self.assert_platform_metrics(self.platform_metrics, 3, 200)

    def test_update_listing_updates_metrics_with_listing_status_active_no_price_change_for_single_user(self):
        self.listing.name = "New Name"
        self.listing.save()
        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 1, 50)
        self.assert_city_metrics(self.city_metrics, 1, 50)
        self.assert_platform_metrics(self.platform_metrics, 2, 100)

    def test_update_listing_updates_metrics_with_listing_status_active_price_change_for_single_user(self):
        user_listing = Listing.objects.get(user=self.user)
        user_listing.price = 100
        user_listing.save()
        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 1, 100)
        self.assert_city_metrics(self.city_metrics, 1, 100)
        self.assert_platform_metrics(self.platform_metrics, 2, 150)

    def test_update_listing_updates_metrics_change_listing_status_pending_no_price_change_for_single_user(self):
        user_listing = Listing.objects.get(user=self.user)
        user_listing.status = self.pending_status
        user_listing.save()
        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 0, 0, 1, 50)
        self.assert_city_metrics(self.city_metrics,  1, 50)
        self.assert_platform_metrics(self.platform_metrics, 1, 50, 1, 50)

    def test_update_listing_updates_metrics_change_listing_status_pending_price_change_for_single_user(self):
        user_listing = Listing.objects.get(user=self.user)
        user_listing.price = 100
        user_listing.status = self.pending_status
        user_listing.save()
        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 0, 0, 1, 100)
        self.assert_city_metrics(self.city_metrics,  1, 100)
        self.assert_platform_metrics(self.platform_metrics, 1, 50, 1, 100)

    def test_update_listing_updates_metrics_change_listing_status_settled_no_price_change_for_single_user(self):
        user_listing = Listing.objects.get(user=self.user)
        user_listing.status = self.settled_status
        user_listing.save()
        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 0, 0, 0, 0, 1, 50)
        self.assert_city_metrics(self.city_metrics, 1, 50)
        self.assert_platform_metrics(self.platform_metrics, 1, 50, 0, 0, 1, 50)

    def test_update_listing_updates_metrics_change_listing_status_settled_price_change_for_single_user(self):
        user_listing = Listing.objects.get(user=self.user)
        user_listing.price = 100
        user_listing.status = self.settled_status
        user_listing.save()
        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 0, 0, 0, 0, 1, 100)
        self.assert_city_metrics(self.city_metrics, 1, 100)
        self.assert_platform_metrics(self.platform_metrics, 1, 50, 0, 0, 1, 100)

    def test_delete_listing_update_metrics_with_active_listing_for_single_user(self):
        user_listing = Listing.objects.get(user=self.user)
        user_listing.delete()
        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 0, 0)
        self.assert_city_metrics(self.city_metrics, 0, 0)
        self.assert_platform_metrics(self.platform_metrics, 1, 50)

    def test_delete_listing_update_metrics_with_pending_listing_for_single_user(self):
        user_listing = Listing.objects.get(user=self.user)
        user_listing.status = self.pending_status
        user_listing.save()
        user_listing.delete()
        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 0, 0, 0, 0)
        self.assert_city_metrics(self.city_metrics, 0, 0)
        self.assert_platform_metrics(self.platform_metrics, 1, 50)

    def test_delete_listing_update_metrics_with_settled_listing_for_single_user(self):
        user_listing = Listing.objects.get(user=self.user)
        user_listing.status = self.settled_status
        user_listing.save()
        user_listing.delete()
        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 0, 0, 0, 0, 0, 0)
        self.assert_city_metrics(self.city_metrics, 0, 0)
        self.assert_platform_metrics(self.platform_metrics, 1, 50)

    # Check two users now
        new_listing_for_user = Listing.objects.create(
            user=self.user,
            listing_type=self.listing_type,
            name=self.name,
            description=self.description,
            category=self.category,
            condition=self.condition,
            price=200,
            meetup_point=self.meetup_point,
            status=self.active_status
        )

        new_listing_for_another_user = Listing.objects.create(
            user=self.another_user,
            listing_type=self.listing_type,
            name=self.name,
            description=self.description,
            category=self.category,
            condition=self.condition,
            price=350,
            meetup_point=self.meetup_point,
            status=self.active_status
        )

        self.refresh_metrics()

        self.assert_user_metrics(self.user_metrics, 1, 200)
        self.assert_user_metrics(self.another_user_metrics, 2, 400)
        self.assert_city_metrics(self.city_metrics, 1, 200)
        self.assert_city_metrics(self.another_city_metrics, 2, 400)
        self.assert_platform_metrics(self.platform_metrics, 3, 600)

    def test_update_listing_updates_metrics_with_listing_status_active_price_change_for_both_users_in_two_cities(self):
        """Test that updating a listing for the first user updates the metrics."""
        user_listing = Listing.objects.get(user=self.user)
        user_listing.price = 100
        user_listing.save()

        another_user_listing = Listing.objects.get(user=self.another_user)
        another_user_listing.price = 200
        another_user_listing.save()

        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 1, 100)
        self.assert_user_metrics(self.another_user_metrics, 1, 200)
        self.assert_city_metrics(self.city_metrics, 1, 100)
        self.assert_city_metrics(self.another_city_metrics, 1, 200)
        self.assert_platform_metrics(self.platform_metrics, 2, 300)

    def test_update_listing_updates_metrics_with_listing_status_pending_price_change_for_both_users_in_two_cities(self):
        """Test that updating a listing for the first user; updates the metrics."""
        self.update_listing(self.user, price=100, status=self.pending_status)
        self.update_listing(self.another_user, price=200, status=self.pending_status)
        self.refresh_metrics()

        self.assert_user_metrics(self.user_metrics, 0, 0, 1, 100)
        self.assert_user_metrics(self.another_user_metrics, 0, 0, 1, 200)
        self.assert_city_metrics(self.city_metrics, 1, 100)
        self.assert_city_metrics(self.another_city_metrics, 1, 200)
        self.assert_platform_metrics(self.platform_metrics, 0, 0, 2, 300)

    def test_update_listing_updates_metrics_with_listing_status_settled_price_change_for_both_users_in_two_cities(self):
        """Test that updating a listing for the first user; updates the metrics."""
        self.update_listing(self.user, price=100, status=self.settled_status)
        self.update_listing(self.another_user, price=200, status=self.settled_status)
        self.refresh_metrics()

        self.assert_user_metrics(self.user_metrics, 0, 0, 0, 0, 1, 100)
        self.assert_user_metrics(self.another_user_metrics, 0, 0, 0, 0, 1, 200)
        self.assert_city_metrics(self.city_metrics,  1, 100)
        self.assert_city_metrics(self.another_city_metrics,  1, 200)
        self.assert_platform_metrics(self.platform_metrics, 0, 0, 0, 0, 2, 300)

    def test_delete_listing_update_metrics_for_both_users(self):
        """Test that deleting a listing for the first user; updates the metrics."""
        user_listing = Listing.objects.get(user=self.user)
        user_listing.delete()

        another_user_listing = Listing.objects.get(user=self.another_user)
        another_user_listing.delete()

        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 0, 0)
        self.assert_user_metrics(self.another_user_metrics, 0, 0)
        self.assert_city_metrics(self.city_metrics, 0, 0)
        self.assert_city_metrics(self.another_city_metrics, 0, 0)
        self.assert_platform_metrics(self.platform_metrics, 0, 0)

    def test_metrics_update_on_user_soft_deletion(self):
        self.user.soft_delete()
        self.refresh_metrics()
        self.assert_user_metrics(self.user_metrics, 0, 0)
        self.assert_city_metrics(self.city_metrics, 0,  0)
        self.assert_platform_metrics(self.platform_metrics, 1,  50)
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deleted_at)

    def test_migrate_listing_to_another_city_updates_metrics(self):
        user_listing = Listing.objects.get(user=self.user)
        user_listing.city = self.another_city
        user_listing.save()

        self.refresh_metrics()

        self.assert_user_metrics(self.user_metrics, 1, 50)
        self.assert_city_metrics(self.another_city_metrics, 1, 50)
        self.assert_platform_metrics(self.platform_metrics, 2, 100)
        # Only university's city will be counted, due to the ER relationship
        # Also, the app does not support multiple universities for a user (assumption made)


class ConcurrencyTestCase(ListingBaseMetricsTestCase):
    """Test that updating listings for both users concurrently updates the metrics correctly."""

    def test_concurrent_listing_updates(self):
        self.refresh_metrics()

        # Create a lock to synchronize access to the metrics and listings
        lock = threading.Lock()

        # Define a function for concurrent updates
        def update_listing_price(listing, new_price):
            with lock:
                listing.price = new_price
                listing.save()
                self.refresh_metrics()

        # Get the user's listing and another user's listing
        user_listing = Listing.objects.get(user=self.user)
        another_user_listing = Listing.objects.get(user=self.another_user)

        # Create threads for concurrent updates
        thread1 = threading.Thread(target=update_listing_price, args=(user_listing, 75))
        thread2 = threading.Thread(target=update_listing_price, args=(another_user_listing, 150))

        thread1.start()
        thread2.start()

        # Wait for threads to finish
        thread1.join()
        thread2.join()

        self.assert_user_metrics(self.user_metrics, 1,  75)
        self.assert_user_metrics(self.another_user_metrics, 1,  150)
        self.assert_city_metrics(self.city_metrics, 1,  75)
        self.assert_city_metrics(self.another_city_metrics, 1,  150)
        self.assert_platform_metrics(self.platform_metrics, 2,  225)
