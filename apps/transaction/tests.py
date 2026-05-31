import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from .services import generate_unique_hash, get_actual_date, process_description

User = get_user_model()


# Create your tests here.
class TestGenerateUniqueHash(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="testuser@example.com", password="testpass123"
        )

    def test_unique_hash_processes_correctly(self):
        description = "SUPA IGA - Visa Purchase - Receipt 124511Date 08 May 2026"
        amount = -20.26
        balance = 50.00

        identifier = generate_unique_hash(description, amount, balance, self.user.uid)
        expected_identifier = f"124511_20_26{self.user.uid}"

        self.assertEqual(identifier, expected_identifier)

    def test_without_reciept_number(self):
        description = "SUPA IGA - Visa Purchase - Date 08 May 2026"
        amount = -20.26
        balance = 50.00

        identifier = generate_unique_hash(description, amount, balance, self.user.uid)
        expected_identifier = f"124511_20_26{self.user.uid}"

        self.assertEqual(identifier, expected_identifier)

    def test_with_negative_balance_and_amount(self):
        description = "SUPA IGA - Visa Purchase - Receipt 124511Date 08 May 2026"
        amount = -20.26
        balance = -50.00

        identifier = generate_unique_hash(description, amount, balance, self.user.uid)
        expected_identifier = f"124511_20_26{self.user.uid}"

        self.assertEqual(identifier, expected_identifier)

    def test_with_five_number_receipt_number(self):
        description = "SUPA IGA - Visa Purchase - Receipt 12451Date 08 May 2026"
        amount = -20.26
        balance = 50.00

        identifier = generate_unique_hash(description, amount, balance, self.user.uid)
        expected_identifier = f"12451_20_26{self.user.uid}"

        self.assertEqual(identifier, expected_identifier)


class TestProcessDescription(TestCase):
    def test_correctly_processes_standard_description(self):
        description = (
            "CX - Visa Purchase - Receipt 130360Date 20 May 2026 Card xxxxxxxxxxxxxxxx"
        )

        vendor, purchase_type, receipt_details = process_description(description)

        self.assertEqual(vendor, "CX")
        self.assertEqual(purchase_type, "Visa Purchase")
        self.assertEqual(
            receipt_details, "Receipt 130360Date 20 May 2026 Card xxxxxxxxxxxxxxxx"
        )

    def test_processes_blank_description_as_blank(self):
        description = ""

        vendor, purchase_type, receipt_details = process_description(description)

        self.assertEqual(vendor, "")
        self.assertEqual(purchase_type, "")
        self.assertEqual(receipt_details, "")

    def test_processes_description_with_no_purchase_type(self):
        description = "MCARE BENEFITS   335139846 IYWQ  - Receipt 120800"

        vendor, purchase_type, receipt_details = process_description(description)

        self.assertEqual(vendor, "MCARE BENEFITS   335139846 IYWQ")
        self.assertEqual(purchase_type, "")
        self.assertEqual(receipt_details, "Receipt 120800")

    def test_processes_description_with_no_purchase_type_or_reciept_details(self):
        description = "Utility Bill Cashback"

        vendor, purchase_type, receipt_details = process_description(description)

        self.assertEqual(vendor, "Utility Bill Cashback")
        self.assertEqual(purchase_type, "")
        self.assertEqual(receipt_details, "")


class TestGetActualDate(TestCase):
    def test_get_date_from_description(self):
        description = "Receipt 130360Date 20 May 2026 Card xxxxxxxxxxxxxxxx"

        date = get_actual_date(description)

        self.assertEqual(date, datetime.date(2026, 5, 20))

    def test_get_date_returns_none_with_invalid_date(self):
        description = "Receipt 130360Date 40 May 2026 Card xxxxxxxxxxxxxxxx"

        date = get_actual_date(description)

        self.assertEqual(date, None)

    def test_returns_none_with_no_date_in_description(self):
        description = "Receipt 130360 Card xxxxxxxxxxxxxxxx"

        date = get_actual_date(description)

        self.assertEqual(date, None)
