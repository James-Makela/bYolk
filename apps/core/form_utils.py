from typing import Any

from django import forms
from django.db.models import QuerySet


def limit_queryset(
    form: forms.BaseForm,
    field_name: str,
    queryset: QuerySet[Any],
) -> None:
    field = form.fields[field_name]
    if not isinstance(field, forms.ModelChoiceField):
        raise TypeError(f"{field_name} is not a ModelChoiceField")
    field.queryset = queryset
