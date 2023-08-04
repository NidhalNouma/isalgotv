from django.db import models
from django.contrib.auth.models import User

from ckeditor.fields import RichTextField

# Create your models here.

class StrategyImages(models.Model):
    name = models.CharField(max_length=100)
    img = models.ImageField(upload_to='strategies_images/')
    created_at = models.DateTimeField(auto_now_add=True)

class StrategyComments(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    imagees = models.ManyToManyField(StrategyImages)
    description = models.TextField()

class StrategyResults(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    imagees = models.ManyToManyField(StrategyImages)
    settings = models.JSONField(default=dict)
    description = models.TextField()


    TIME_FRAME = [
        ("S", "Seconds"),
        ("M", "Minutes"),
        ("H", "Hours"),
        ("W", "Weeks"),
        ("Mn", "Months"),
        ("R", "Range"),
    ]

    test_start_at = models.DateTimeField()
    test_end_at = models.DateTimeField()
    time_frame_int = models.IntegerField(default=1)
    time_frame = models.CharField(max_length=2, choices=TIME_FRAME, default="M")

    pair = models.CharField(max_length=100)
    net_profit = models.DecimalField(decimal_places=2, max_digits=2)
    net_profit_percentage = models.DecimalField(decimal_places=2, max_digits=2)
    max_drawdown = models.DecimalField(decimal_places=2, max_digits=2)
    max_drawdown_percentage = models.DecimalField(decimal_places=2, max_digits=2)
    profit_factor = models.DecimalField(decimal_places=5, max_digits=5)
    profitable_percentage = models.DecimalField(decimal_places=2, max_digits=2)
    total_trade = models.IntegerField()

class Strategy(models.Model):
    TYPE = [
        ("S", "Strategy"),
        ("I", "Indicator"),
    ]
     
    type = models.CharField(max_length=1, choices=TYPE, default="S")
    version = models.CharField(max_length=10, default="1.0")
    name = models.CharField(max_length=100)
    description = models.TextField()
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tradingview_ID = models.CharField(max_length=100)
    tradingview_url = models.URLField(blank=True)
    imagees = models.ManyToManyField(StrategyImages)
    results = models.ManyToManyField(StrategyResults)
    video_url = models.URLField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    settings = models.JSONField(default=dict)
    settings_types = models.JSONField(default=dict)
    

    def __str__(self):
        return self.name
    
