from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Category, UserPreferences

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "color"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "color": forms.ColorInput(attrs={"class": "input input-bordered w-full"}),
        }


class InitialUserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ["frequency_value", "frequency_unit", "first_budget_date"]
        widgets = {
            "frequency_value": forms.NumberInput(attrs={"class": "input grow w-full"}),
            "frequency_unit": forms.Select(
                attrs={"class": "select select-bordered w-full"}
            ),
            "first_budget_date": forms.DateInput(
                attrs={"class": "input input-bordered w-full", "type": "date"}
            ),
        }
        labels = {
            "frequency_value": "Every",
            "frequency_unit": "",
        }
