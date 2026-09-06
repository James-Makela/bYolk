from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseModelFormSet, modelformset_factory

from apps.budget.models import Bucket, CostAllocation, IncomeAllocation
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
        fields = [
            "name",
            "expected_amount",
            "amount",
            "expected_date",
            "category",
            "cost",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "expected_amount": forms.NumberInput(
                attrs={"class": "grow w-full", "step": "0.01", "placeholder": "0.00"}
            ),
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


class BucketForm(forms.ModelForm):
    class Meta:
        model = Bucket
        fields = ["name", "cost"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered w-full"}),
            "cost": forms.Select(attrs={"class": "select select-bordered w-full"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(BucketForm, self).__init__(*args, **kwargs)
        if user:
            self.fields["cost"].queryset = Cost.objects.filter(user=user)


class BucketEmptyForm(forms.ModelForm):
    selected = forms.BooleanField(required=False)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False)

    class Meta:
        model = CostAllocation
        fields = []

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("selected") and cleaned.get("amount") is None:
            raise ValidationError("Amount is required.")
        return cleaned


class BaseBucketEmptyFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        selected = [form for form in self.forms if form.cleaned_data.get("selected")]
        if not selected:
            raise ValidationError("Select at least one allocation.")


BucketEmptyFormSet = modelformset_factory(
    CostAllocation,
    form=BucketEmptyForm,
    formset=BaseBucketEmptyFormSet,
    extra=0,
)
