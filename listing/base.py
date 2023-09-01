from listing.models import ListingType, Category, Condition, MeetupPoint, Status
from django.test import TestCase

from metrics.models import UserMetrics, CityMetrics, PlatformMetrics
from user.models import City, CustomUser

# Constants:
TEST_EMAIL = 'test@uni.ac.uk'
TEST_PASSWORD = 'testpassword123'


class BaseTest(TestCase):
    def setup_common_data(self):
        self.listing_type = ListingType.objects.create(name="Test Listing Type")
        self.name = "Test Title"
        self.description = "Test Description"
        self.category = Category.objects.create(name="Test Category")
        self.condition = Condition.objects.create(name="Test Condition")
        self.price = 50
        self.meetup_point = MeetupPoint.objects.create(name="Test Meetup Point")
        self.active_status = Status.objects.create(name="Active")

    def setup_users(self):
        self.city = City.objects.create(name="Test City")
        self.another_city = City.objects.create(name="Another Test City")
        self.user = CustomUser.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD, city=self.city)
        self.another_user = CustomUser.objects.create_user(email="another_" + TEST_EMAIL, password=TEST_PASSWORD,
                                                           city=self.another_city)

        self.user_metrics = UserMetrics.objects.create(user=self.user)
        self.another_user_metrics = UserMetrics.objects.create(user=self.another_user)
        self.city_metrics, _ = CityMetrics.objects.get_or_create(city=self.city)
        self.another_city_metrics, _ = CityMetrics.objects.get_or_create(city=self.another_city)
        self.platform_metrics, _ = PlatformMetrics.objects.get_or_create()

    def refresh_metrics(self):
        self.user_metrics.refresh_from_db()
        self.another_user_metrics.refresh_from_db()
        self.city_metrics.refresh_from_db()
        self.another_city_metrics.refresh_from_db()
        self.platform_metrics.refresh_from_db()
