from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import validate_email

class UserCreationEmailForm(UserCreationForm):
    username = forms.EmailField(required=True, validators=[validate_email])

    class Meta:
        model = User
        fields = ("username", "password1", "password2")
