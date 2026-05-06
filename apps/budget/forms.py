from django import forms

from apps.budget.models import CostAllocation


class CostAllocationForm(forms.ModelForm):
    class Meta:
        model = CostAllocation
        fields = ["cost_name", "cost_amount"]
        widgets = {
            "cost_name": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "cost_amount": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
        }
