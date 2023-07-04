from django.forms import ModelForm
from .models import User_Profile
from django import forms

class User_ProfileForm(ModelForm):
    class Meta:
        model = User_Profile
        fields = ['profile_pic', 'tradingview_username', 'bio']
        # fields = '__all__'


class PaymentCardForm(forms.Form):
    card_name = forms.CharField(label="cardName", max_length=100)
    card_number = forms.CharField(label="cardNumber", max_length=16)
    card_exp_year = forms.CharField(label="cardExpYear", max_length=4)
    card_exp_month = forms.CharField(label="cardExpMonth", max_length=2)
    card_cvc = forms.CharField(label="cardCVC", max_length=3)


    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')

        if not card_number.isdigit():
            raise forms.ValidationError('Card number should only contain numbers.')
        
        if len(card_number) != 16:
            raise forms.ValidationError('Card number must be exactly 16 characters long.')

        return card_number

    def clean_card_cvc(self):
        card_cvc = self.cleaned_data.get('card_cvc')

        if not card_cvc.isdigit():
            raise forms.ValidationError('Card CVC should only contain numbers.')

        if len(card_cvc) != 3:
            raise forms.ValidationError('Card CVC must be exactly 3 characters long.')

        return card_cvc