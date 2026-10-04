from typing import Any

from django import forms

from apps.core.form_utils import limit_queryset
from apps.core.models import Category

from .models import Cost


class CostForm(forms.ModelForm["Cost"]):
    class Meta:
        model = Cost
        fields = [
            "name",
            "amount",
            "category",
            "keywords",
            "frequency_value",
            "frequency_unit",
            "start_date",
            "end_date",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "amount": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
            "category": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "keywords": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Netflix, NFLX, Spotify",
                    "class": "input input-bordered w-full",
                }
            ),
            "frequency_value": forms.NumberInput(attrs={"class": "input grow w-full"}),
            "frequency_unit": forms.Select(
                attrs={"class": "select select-bordered w-full"}
            ),
            "start_date": forms.DateInput(
                attrs={"class": "input input-bordered w-full", "type": "date"},
                format="%Y-%m-%d",
            ),
            "end_date": forms.DateInput(
                attrs={"class": "input input-bordered w-full", "type": "date"},
                format="%Y-%m-%d",
            ),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        limit_queryset(self, "category", Category.objects.filter(user=user))
        if user and hasattr(user, "preferences"):
            self.fields["start_date"].initial = user.preferences.first_budget_date
