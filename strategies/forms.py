from django import forms
from .models import StrategyComments, Replies, StrategyResults

class StrategyCommentForm(forms.ModelForm):
    class Meta:
        model = StrategyComments
        fields = ['description']  # Add any other fields you want

class StrategyResultForm(forms.ModelForm):
    class Meta:
        model = StrategyResults
        exclude = ['replies, images', 'created_by', 'created_at']
        # fields = ['description', 'settings', 'pair', 'net_profit', 'net_profit_percentage', 'max_drawdown', 'max_drawdown_percentage', 'profit_factor', 'profitable_percentage', 'total_trade', "test_start_at", "test_end_at", "time_frame_int", "time_frame"]  # Add any other fields you want

class RepliesForm(forms.ModelForm):
    class Meta:
        model = Replies
        fields = ['description']  # Add any other fields you want

    