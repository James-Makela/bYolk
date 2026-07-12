from django import forms

from .models import PropertyAsset, SavingsAccount


class PropertyForm(forms.ModelForm):
    class Meta:
        model = PropertyAsset
        fields = [
            "name",
            "amount_owing",
            "value",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "amount_owing": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
            "value": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
        }


class SavingsForm(forms.ModelForm):
    class Meta:
        model = SavingsAccount
        fields = [
            "name",
            "interest_rate",
            "value",
            "is_primary",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "interest_rate": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
            "value": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
            "is_primary": forms.CheckboxInput(
                attrs={"class": "checkbox checkbox-sm m-2"}
            ),
        }
