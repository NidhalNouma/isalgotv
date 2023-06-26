from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class StrategyImages(models.Model):
    name = models.CharField(max_length=100)
    img = models.ImageField(upload_to='strategies_images/')
    created_at = models.DateTimeField(auto_now_add=True)

class Strategy(models.Model):
    TYPE = [
        ("S", "Strategy"),
        ("I", "Indicator"),
    ]
     
    type = models.CharField(max_length=1, choices=TYPE, default="S")
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tradingview_ID = models.CharField(max_length=100)
    tradingview_url = models.URLField(blank=True)
    imagees = models.ManyToManyField(StrategyImages)
    video_url = models.URLField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    

    def __str__(self):
        return self.name
    

