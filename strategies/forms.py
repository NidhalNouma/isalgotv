from django import forms
from .models import StrategyComments

class StrategyCommentForm(forms.ModelForm):
    class Meta:
        model = StrategyComments
        fields = ['description']  # Add any other fields you want

    