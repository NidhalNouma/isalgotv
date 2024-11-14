from django import forms
from .models import StrategyComments, Replies, StrategyResults
from django.core.exceptions import ValidationError

class StrategyCommentForm(forms.ModelForm):
    class Meta:
        model = StrategyComments
        fields = ['description']  # Add any other fields you want

class StrategyResultForm(forms.ModelForm):
    class Meta:
        model = StrategyResults
        exclude = ['replies, images', 'created_by', 'created_at', "version"]
        # fields = ['description', 'settings', 'pair', 'net_profit', 'net_profit_percentage', 'max_drawdown', 'max_drawdown_percentage', 'profit_factor', 'profitable_percentage', 'total_trade', "test_start_at", "test_end_at", "time_frame_int", "time_frame"]  # Add any other fields you want

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 200:
            raise ValidationError('Description needs to be at least 200 characters.')
        return description

    def clean_profit_factor(self):
        profit_factor = self.cleaned_data.get('profit_factor')
        if profit_factor <= 1.35:
            raise ValidationError('Unfortunately this result cannot be accepted. The result provided did not meet our requirement.')
        return profit_factor

class RepliesForm(forms.ModelForm):
    class Meta:
        model = Replies
        fields = ['description']  # Add any other fields you want

    