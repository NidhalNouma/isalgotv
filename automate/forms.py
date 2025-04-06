from django import forms
from .models import *
from django.core.exceptions import ValidationError


class AddCryptoBrokerAccountForm(forms.ModelForm):
    class Meta:
        model = CryptoBrokerAccount
        exclude = ['active', 'custom_id', 'created_at']
        # fields = ['description', 'settings', 'pair', 'net_profit', 'net_profit_percentage', 'max_drawdown', 'max_drawdown_percentage', 'profit_factor', 'profitable_percentage', 'total_trade', "test_start_at", "test_end_at", "time_frame_int", "time_frame"]  # Add any other fields you want


class AddForexBrokerAccountForm(forms.ModelForm):
    class Meta:
        model = ForexBrokerAccount
        exclude = ['active', 'custom_id', 'created_at', 'account_api_id']