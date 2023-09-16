from _decimal import Decimal

from listing.base import BaseTest
from .models import PlatformMetrics


class UserContributionRatioTestCase(BaseTest):

    def setUp(self):
        self.setup_common_data()
        self.setup_users()

    def test_user_contribution_ratio(self):
        self.user_metrics.delivery_weight = 30
        self.user_metrics.meetup_weight = 20
        self.user_metrics.save()

        self.city_metrics.delivery_weight = 50
        self.city_metrics.meetup_weight = 50
        self.city_metrics.save()

        self.refresh_metrics()

        # Print the values to debug
        print("City Delivery Weight: ", self.city_metrics.delivery_weight)
        print("City Meetup Weight: ", self.city_metrics.meetup_weight)
        print("User Delivery Weight: ", self.user_metrics.delivery_weight)
        print("User Meetup Weight: ", self.user_metrics.meetup_weight)

        expected_ratio = Decimal("50.00")

        # Print the actual ratio to debug
        actual_ratio = self.user_metrics.calculate_user_contribution_ratio()
        print("Actual Ratio: ", actual_ratio)

        self.assertEqual(actual_ratio, expected_ratio)


class CityContributionRatioTestCase(BaseTest):

    def setUp(self):
        self.setup_common_data()
        self.setup_users()

    def test_city_contribution_ratio(self):
        self.city_metrics.delivery_weight = 50
        self.city_metrics.meetup_weight = 50
        self.city_metrics.save()

        self.platform_metrics.delivery_weight = 200
        self.platform_metrics.meetup_weight = 200
        self.platform_metrics.save()

        self.refresh_metrics()
        expected_ratio = Decimal("25.00")
        self.assertEqual(self.city_metrics.calculate_city_contribution_ratio(), expected_ratio)


class PlatformContributionRatioTestCase(BaseTest):

    def setUp(self):
        self.setup_common_data()
        self.setup_users()

    def test_ratio_calculation_is_accurate_and_rounded(self):
        # Creating a PlatformMetrics instance with known values
        metrics = PlatformMetrics(
            delivery_weight=Decimal('5000.00'),
            meetup_weight=Decimal('2500.00'),
            uk_waste=Decimal('22220000.00')
        )

        # Expected rounded value: 0.03375338
        expected_rounded_ratio = Decimal('0.03375338')

        # Call the method and compare it with expected value
        self.assertEqual(metrics.calculate_platform_contribution_ratio(), expected_rounded_ratio)
