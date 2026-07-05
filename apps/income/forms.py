from django import forms

from .models import Income


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = [
            "name",
            "amount",
            "keywords",
            "frequency_value",
            "frequency_unit",
            "start_date",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "amount": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
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
                attrs={"class": "input input-bordered w-full", "type": "date"}
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(IncomeForm, self).__init__(*args, **kwargs)
        if user and hasattr(user, "preferences"):
            self.fields["start_date"].initial = user.preferences.first_budget_date
