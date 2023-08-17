from django import forms
from .models import StrategyComments, Replies

class StrategyCommentForm(forms.ModelForm):
    class Meta:
        model = StrategyComments
        fields = ['description']  # Add any other fields you want

class RepliesForm(forms.ModelForm):
    class Meta:
        model = Replies
        fields = ['description']  # Add any other fields you want

    