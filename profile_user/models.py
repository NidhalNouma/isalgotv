from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class User_Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics')
    bio = models.TextField(max_length=1000)
    tradingview_username = models.CharField(max_length=100)
    strategies = models.ManyToManyField(to='strategies.Strategy')

    subscription_id = models.CharField(max_length=100)
    customer_id = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username

    def get_tradingview_username(self):
        if self.tradingview_username:
            return self.tradingview_username
        return self.user.username
