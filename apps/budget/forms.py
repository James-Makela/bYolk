from django import forms

from apps.budget.models import CostAllocation, IncomeAllocation
from apps.core.models import Category
from apps.cost.models import Cost
from apps.income.models import Income


class CostAllocationForm(forms.ModelForm):
    class Meta:
        model = CostAllocation
        fields = ["name", "amount", "expected_date", "category"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "amount": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
            "expected_date": forms.DateInput(
                attrs={"class": "input input-bordered w-full", "type": "date"}
            ),
            "category": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(CostAllocationForm, self).__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)


class CostAllocationTransactionsForm(forms.ModelForm):
    class Meta:
        model = CostAllocation
        fields = ["name", "amount", "expected_date", "category", "cost"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "amount": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
            "expected_date": forms.DateInput(
                attrs={"class": "input input-bordered w-full", "type": "date"}
            ),
            "category": forms.Select(attrs={"class": "select select-bordered w-full"}),
            "cost": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(CostAllocationTransactionsForm, self).__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)
            self.fields["cost"].queryset = Cost.objects.filter(user=user)


class IncomeAllocationTransactionsForm(forms.ModelForm):
    class Meta:
        model = IncomeAllocation
        fields = ["name", "amount", "expected_date", "income"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "amount": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
            "expected_date": forms.DateInput(
                attrs={"class": "input input-bordered w-full", "type": "date"}
            ),
            "income": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(IncomeAllocationTransactionsForm, self).__init__(*args, **kwargs)
        if user:
            self.fields["income"].queryset = Income.objects.filter(user=user)
