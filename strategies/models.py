from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User
from profile_user.models import User_Profile

from ckeditor.fields import RichTextField

# Create your models here.



class StrategyImages(models.Model):
    name = models.CharField(max_length=100)
    img = models.ImageField(upload_to='strategies_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

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
    video_url = models.URLField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    settings = models.JSONField(default=dict)
    settings_types = models.JSONField(default=dict)

    images = GenericRelation(StrategyImages) 
    
    def __str__(self):
        return self.name


class Replies(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    description = models.TextField()

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    images = GenericRelation(StrategyImages) 
    replies = GenericRelation('self') 

    
class StrategyComments(models.Model):
    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, blank=True)

    images = GenericRelation(StrategyImages) 
    replies = GenericRelation(Replies) 

class StrategyResults(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, blank=True)
    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    settings = models.JSONField(default=dict)
    description = models.TextField()
    votes = models.IntegerField(default=0)

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
    net_profit = models.DecimalField(decimal_places=2, max_digits=10)
    net_profit_percentage = models.DecimalField(decimal_places=2, max_digits=10)
    max_drawdown = models.DecimalField(decimal_places=2, max_digits=10)
    max_drawdown_percentage = models.DecimalField(decimal_places=2, max_digits=10)
    profit_factor = models.DecimalField(decimal_places=5, max_digits=12)
    profitable_percentage = models.DecimalField(decimal_places=2, max_digits=10)
    total_trade = models.IntegerField()

    images = GenericRelation(StrategyImages) 
    replies = GenericRelation(Replies) 
    