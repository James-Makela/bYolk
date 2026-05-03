from django import forms
from .models import Cost

class CostForm(forms.ModelForm):
    class Meta:
        model = Cost
        fields = ['name', 'amount', 'category', 'frequency_value', 'frequency_unit', 'start_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-bordered w-full'}),
            'amount': forms.NumberInput(attrs={'class': 'grow w-full', 'step': '0.01', 'placeholder': '0.00'}),
            'category': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'frequency_value': forms.NumberInput(attrs={'class': 'input grow w-full'}),
            'frequency_unit': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'start_date': forms.DateInput(attrs={'class': 'input input-bordered w-full', 'type': 'date'}),
        }
