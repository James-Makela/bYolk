from django import forms

from apps.budget.models import CostAllocation
from apps.core.models import Category


class CostAllocationForm(forms.ModelForm):
    class Meta:
        model = CostAllocation
        fields = ["cost_name", "cost_amount", "category"]
        widgets = {
            "cost_name": forms.TextInput(
                attrs={"class": "input input-bordered w-full"}
            ),
            "cost_amount": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
            "category": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(CostAllocationForm, self).__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)
