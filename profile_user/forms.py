from django.forms import ModelForm
from .models import User_Profile

class User_ProfileForm(ModelForm):
    class Meta:
        model = User_Profile
        fields = ['profile_pic', 'bio', 'tradingview_username']
        # fields = '__all__'

