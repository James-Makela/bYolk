from datetime import datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Category, FrequencyMixin, UserPreferences

User = get_user_model()


class CustomUserTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="test",
            email="test@test.com",
            password="testpass123",
        )
        self.assertEqual(user.username, "test")
        self.assertEqual(user.email, "test@test.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username="supertest",
            email="supertest@test.com",
            password="supertestpass123",
        )
        self.assertEqual(user.username, "supertest")
        self.assertEqual(user.email, "supertest@test.com")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class SignupPageTests(TestCase):
    username = "newuser"
    email = "newuser@email.com"

    @classmethod
    def setUp(self):
        url = reverse("register")
        self.response = self.client.get(url)

    def test_signup_template(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, "registration/register.html")
        self.assertContains(self.response, "Create Account")
        self.assertNotContains(self.response, "Some text that should no be on the page")

    def test_signup_form(self):
        User.objects.create_user(self.username, self.email)
        self.assertEqual(get_user_model().objects.all().count(), 1)
        self.assertEqual(get_user_model().objects.all()[0].username, self.username)
        self.assertEqual(get_user_model().objects.all()[0].email, self.email)


class FrequencyTestModel(FrequencyMixin):
    class Meta:
        app_label = "apps.core"


class FrequencyMixinTests(TestCase):
    def make_frequency(self, value, unit):
        return FrequencyTestModel(frequency_value=value, frequency_unit=unit)

    def test_yearly(self):
        frequency_instance = self.make_frequency(1, "years")
        start_date = datetime(2024, 1, 1)

        self.assertEqual(frequency_instance.frequency_string(), "Every Year")
        self.assertEqual(
            start_date + frequency_instance.get_delta(), datetime(2025, 1, 1)
        )

    def test_every_two_weeks(self):
        frequency_instance = self.make_frequency(2, "weeks")
        start_date = datetime(2025, 3, 1)

        self.assertEqual(frequency_instance.frequency_string(), "Every 2 Weeks")
        self.assertEqual(
            start_date + frequency_instance.get_delta(), datetime(2025, 3, 15)
        )
        self.assertEqual(
            start_date + (3 * frequency_instance.get_delta()), datetime(2025, 4, 12)
        )

    def test_monthly(self):
        frequency_instance = self.make_frequency(1, "months")
        start_date = datetime(2026, 1, 31)

        self.assertEqual(frequency_instance.frequency_string(), "Every Month")
        # Test february is handled correctly
        self.assertEqual(
            start_date + frequency_instance.get_delta(), datetime(2026, 2, 28)
        )
        # Test rolls over correctly to the following month
        self.assertEqual(
            start_date + (2 * frequency_instance.get_delta()), datetime(2026, 3, 31)
        )

    def test_every_three_days(self):
        frequency_instance = self.make_frequency(3, "days")
        start_date = datetime(2024, 1, 1)

        self.assertEqual(frequency_instance.frequency_string(), "Every 3 Days")
        # Tests leap years are handled correctly
        self.assertEqual(
            start_date + (100 * frequency_instance.get_delta()), datetime(2024, 10, 27)
        )

    def test_equality(self):
        frequency_instance_one = self.make_frequency(14, "days")
        frequency_instance_two = self.make_frequency(2, "weeks")

        self.assertTrue(
            frequency_instance_one.matches_frequency(frequency_instance_two)
        )


class UserPreferencesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", password="testpass123")

    def test_next_pay_date(self):
        preferences = UserPreferences.objects.create(
            user=self.user,
            frequency_value=2,
            frequency_unit="weeks",
            first_budget_date=datetime(2026, 1, 1),
        )

        next_pay_date = preferences.first_budget_date + preferences.get_delta()
        self.assertEqual(next_pay_date, datetime(2026, 1, 15))

    def test_default_values(self):
        preferences = UserPreferences.objects.create(user=self.user)

        self.assertEqual(preferences.user, self.user)
        self.assertEqual(preferences.frequency_value, 1)
        self.assertEqual(preferences.frequency_unit, "months")
        self.assertIsNotNone(preferences.first_budget_date)
        self.assertEqual(self.user.preferences, preferences)

    def test_multiple_preferences_for_one_user_raises_integrityerror(self):
        UserPreferences.objects.create(user=self.user)
        with self.assertRaises(IntegrityError):
            UserPreferences.objects.create(user=self.user)

    def test_preferences_string(self):
        preferences = UserPreferences.objects.create(user=self.user)

        self.assertEqual(str(preferences), "Preferences for testuser")


class CategoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        cls.category = Category.objects.create(user=cls.user, name="Transport")

    def test_category_string(self):
        self.assertEqual(str(self.category), "Transport")

    def test_verbose_name_plural(self):
        self.assertEqual(str(Category._meta.verbose_name_plural), "Categories")

    def test_user_cannot_create_duplicate_category(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(user=self.user, name="Transport")

    def test_duplicate_category_protection_is_case_sensitive(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(user=self.user, name="transport")

    def test_another_user_can_create_same_category(self):
        user_two = User.objects.create_user(
            username="anothertestuser",
            password="testpass124",
        )
        category_two = Category.objects.create(
            user=user_two,
            name="Transport",
        )

        self.assertEqual(self.category.name, category_two.name)
        self.assertNotEqual(self.category.user, category_two.user)
