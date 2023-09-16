from django.test import TestCase

from .forms import CustomUserCreationForm, LoginForm, CustomPasswordChangeForm, UserProfileForm
from .models import City, University, CustomUser
from django.urls import reverse

# Constants:
TEST_EMAIL = 'test@uni.ac.uk'
TEST_PASSWORD = 'testpassword123'


class BaseTestCase(TestCase):
    """Base Test case to be inherited by other test classes"""

    def setUp(self):
        """Set up common test data"""
        self.city = City.objects.create(name="Test City")
        self.university = University.objects.create(name="Test University", city=self.city)
        self.user = CustomUser.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)

    def login_user(self):
        """Utility method to login user"""
        self.client.login(email=TEST_EMAIL, password=TEST_PASSWORD)


class CityModelTest(BaseTestCase):
    """Models tests with CRUD operations for City"""

    def test_create_city(self):
        self.assertEqual(self.city.name, "Test City")

    def test_update_city(self):
        self.city.name = "Updated City"
        self.city.save()
        self.assertEqual(City.objects.get(id=self.city.id).name, "Updated City")

    def test_delete_city_with_university(self):
        # Ensure there's a university associated with the city
        University.objects.create(name="Test University 2", city=self.city)

        self.city.delete()
        # Instead of checking if the city was deleted, check if it still exists
        city_exists = City.objects.filter(id=self.city.id).exists()
        self.assertTrue(city_exists)


class UniversityModelTest(BaseTestCase):
    """Models tests with CRUD operations for University"""

    def test_create_university(self):
        self.assertEqual(self.university.name, "Test University")

    def test_update_university(self):
        self.university.name = "Updated University"
        self.university.save()
        self.assertEqual(University.objects.get(id=self.university.id).name, "Updated University")

    def test_delete_university(self):
        university_id = self.university.id
        self.university.delete()
        with self.assertRaises(University.DoesNotExist):
            University.objects.get(id=university_id)


class CustomUserModelTest(BaseTestCase):
    """Models tests with CRUD operations for CustomUser"""

    def test_create_user(self):
        self.assertEqual(self.user.email, TEST_EMAIL)

    def test_update_user(self):
        self.user.first_name = "Sam"
        self.user.save()
        self.assertEqual(CustomUser.objects.get(id=self.user.id).first_name, "Sam")

    def test_delete_user(self):
        user_id = self.user.id
        self.user.delete()
        with self.assertRaises(CustomUser.DoesNotExist):
            CustomUser.objects.get(id=user_id)


class CustomUserCreationFormTest(BaseTestCase):

    def test_valid_form(self):
        """Tests if form is valid with correct data"""
        data = {'email': 'newuser@uni.ac.uk', 'password1': 'newpassword123', 'password2': 'newpassword123',
                'university': self.university
                }
        form = CustomUserCreationForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        """Tests if form is invalid with mismatched passwords"""
        data = {'email': 'newuser@uni.ac.uk', 'password1': 'newpassword123', 'password2': 'differentpassword',
                'university': self.university}
        form = CustomUserCreationForm(data)
        self.assertFalse(form.is_valid())


class LoginFormTest(BaseTestCase):

    def test_valid_login_form(self):
        """Tests if login form is valid with correct credentials"""
        data = {'email': TEST_EMAIL, 'password': TEST_PASSWORD}
        form = LoginForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_login_form(self):
        """Tests if login form is invalid with wrong credentials"""
        data = {'email': TEST_EMAIL, 'password': 'wrongpassword'}
        form = LoginForm(data)
        self.assertFalse(form.is_valid())


class CustomPasswordChangeFormTest(BaseTestCase):

    def test_valid_password_change(self):
        """Tests if password change form is valid with correct old password"""
        data = {'old_password': TEST_PASSWORD, 'new_password1': 'newpassword321', 'new_password2': 'newpassword321'}
        form = CustomPasswordChangeForm(user=self.user, data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_password_change(self):
        """Tests if password change form is invalid with wrong old password"""
        data = {'old_password': 'wrongoldpassword', 'new_password1': 'newpassword321',
                'new_password2': 'newpassword321'}
        form = CustomPasswordChangeForm(user=self.user, data=data)
        self.assertFalse(form.is_valid())


class UserProfileFormTest(BaseTestCase):

    def test_valid_profile_form(self):
        """Tests if user profile form is valid with correct data"""
        self.user.university = self.university
        self.user.save()
        data = {'first_name': 'New', 'last_name': 'Test', 'bio': 'Test bio', 'university': self.user.university,
                'move_out_date': '2023-12-31'}
        form = UserProfileForm(instance=self.user, data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_profile_form(self):
        """Tests if user profile form is invalid with missing data"""
        self.user.university = self.university
        self.user.save()
        data = {'first_name': '', 'last_name': 'Test', 'bio': 'Test bio', 'university': self.user.university,
                'move_out_date': '2020-01-01'}
        form = UserProfileForm(instance=self.user, data=data)
        self.assertFalse(form.is_valid())


class ViewsTestCase(BaseTestCase):

    def test_register_get_request(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_post_request_valid(self):
        response = self.client.post(reverse('register'), {
            'email': 'newuser@uni.ac.uk',
            'password1': TEST_PASSWORD,
            'password2': TEST_PASSWORD,
            'university': self.university.id
        })
        self.assertRedirects(response, reverse('profile'))
        self.assertEqual(response.status_code, 302)

    def test_login_view_post_request_valid(self):
        response = self.client.post(reverse('login'), {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
        })
        self.assertRedirects(response, reverse('home'))

    def test_login_view_post_request_invalid(self):
        response = self.client.post(reverse('login'), {
            'email': TEST_EMAIL,
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.login_user()
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)
