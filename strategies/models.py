from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from profile_user.models import User_Profile
from django.core.validators import MinLengthValidator

from ckeditor.fields import RichTextField
import jsonschema
import json
from django.core.exceptions import ValidationError

def settings_validator_json(value):
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "display_name": {"type": "string"},
                                "type": {"type": "string"},
                                "default_value": {"type": "string"},
                                "options": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["name", "type", "default_value"]
                        }
                    }
                }
            },
            "required": ["key", "value"]
        }
    }

    try:
        jsonschema.validate(value, schema)
    except jsonschema.ValidationError:
        raise ValidationError('Invalid JSON data.')

class SettingsJSONField(models.JSONField):
    def __init__(self, *args, **kwargs):
        kwargs['validators'] = [settings_validator_json]
        super().__init__(*args, **kwargs)

def update_names(data):
    name_counter = 0  # This counter will keep track of the suffix to append

    def recurse(items):
        nonlocal name_counter
        original_name = ""
        for item in items:
            for entry in item['value']:  
                for setting in entry:
                    setting_name = setting['name']
                    if not original_name:
                        original_name = setting_name
                    if setting['name'].find(f"{original_name}_") == -1: # or setting['name'].count("_") >= 2:
                        setting['name'] = f"{original_name}_{name_counter}"
                    name_counter += 1

    recurse(data)
    return data

def performance_validator_json(value):
    required_keys = [
        # Net profit keys
        "net_profit",
        "net_profit_long",
        "net_profit_short",
        "net_profit_percentage",
        "net_profit_percentage_long",
        "net_profit_percentage_short",

        # Gross profit keys
        "gross_profit",
        "gross_profit_long",
        "gross_profit_short",
        "gross_profit_percentage",
        "gross_profit_percentage_long",
        "gross_profit_percentage_short",

        # Gross loss keys
        "gross_loss",
        "gross_loss_long",
        "gross_loss_short",
        "gross_loss_percentage",
        "gross_loss_percentage_long",
        "gross_loss_percentage_short",

        # Max drawdown
        "max_drawdown",
        "max_drawdown_percentage",

        # Profit factor
        "profit_factor",
        "profit_factor_long",
        "profit_factor_short",

        # Profitable percentage
        "profitable_percentage",
        "profitable_percentage_long",
        "profitable_percentage_short",

        # Total trade keys
        "total_trade",
        "total_trade_long",
        "total_trade_short",

        # Winning and losing trades
        "winning_total_trade",
        "winning_total_trade_long",
        "winning_total_trade_short",
        "losing_total_trade",
        "losing_total_trade_long",
        "losing_total_trade_short",

        # Average trade keys
        "avg_trade",
        "avg_trade_long",
        "avg_trade_short",
        "avg_trade_percentage",
        "avg_trade_percentage_long",
        "avg_trade_percentage_short",

        # Average win trade keys
        "avg_win_trade",
        "avg_win_trade_long",
        "avg_win_trade_short",
        "avg_win_trade_percentage",
        "avg_win_trade_percentage_long",
        "avg_win_trade_percentage_short",

        # Average win trade keys
        "avg_loss_trade",
        "avg_loss_trade_long",
        "avg_loss_trade_short",
        "avg_loss_trade_percentage",
        "avg_loss_trade_percentage_long",
        "avg_loss_trade_percentage_short",

        # Ratio Avg Win / Avg Loss
        "win_loss_avg",
        "win_loss_avg_long",
        "win_loss_avg_short",
    ]

    # Check for missing keys
    missing_keys = [key for key in required_keys if key not in value]
    if missing_keys:
        raise ValidationError(f"Missing required keys: {', '.join(missing_keys)}")

    
class PerferenceJSONField(models.JSONField):
    def __init__(self, *args, **kwargs):
        kwargs['validators'] = [performance_validator_json]
        super().__init__(*args, **kwargs)


class StrategyImages(models.Model):
    def photo_path(instance, filename):
        content_type_name = instance.content_type.model
        object_id = instance.object_id
        instance_id = instance.id
        path = f'{content_type_name}/{object_id}/{instance_id}/{filename}'

        return path

    name = models.CharField(max_length=100)
    img = models.ImageField(upload_to= photo_path)
    created_at = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

# TODO: Adding tags models (tags examples trendline, oscillator, candlestick ...) to search for strategies by tags

class Strategy(models.Model):
    TYPE = [
        ("S", "Strategy"),
        ("I", "Indicator"),
    ]
     
    type = models.CharField(max_length=1, choices=TYPE, default="S")
    version = models.CharField(max_length=10, default="1.0")

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    description = models.TextField()
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tradingview_ID = models.CharField(max_length=100)
    tradingview_url = models.URLField(blank=True)
    video_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    chart_url = models.URLField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    settings = SettingsJSONField()

    likes = models.ManyToManyField(User, related_name='likes', blank=True)

    is_live = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    
    images = GenericRelation(StrategyImages) 
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.slug == '':
            self.slug = slugify(self.name)  # Automatically generates a slug from the name.

        if self.settings:
            if self.is_live == False:
                self.settings = update_names(self.settings)
            
        super(Strategy, self).save(*args, **kwargs)


class Replies(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    description = models.TextField(validators=[
            MinLengthValidator(100, 'Comment must contain at least 100 characters')
            ])

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    images = GenericRelation(StrategyImages) 
    replies = GenericRelation('self') 

    
class StrategyComments(models.Model):
    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(validators=[
            MinLengthValidator(300, 'Comment must contain at least 300 characters')
            ])
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, blank=True)

    likes = models.ManyToManyField(User, related_name='comment_likes', blank=True)
    dislike = models.ManyToManyField(User, related_name='comment_dislikes', blank=True)

    images = GenericRelation(StrategyImages) 
    replies = GenericRelation(Replies) 

class StrategyResults(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, blank=True)
    created_by = models.ForeignKey(User_Profile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    settings =  SettingsJSONField()
    performance =  PerferenceJSONField()
    description = models.TextField()

    version = models.CharField(max_length=10, default="1.0")

    positive_votes = models.ManyToManyField(User, related_name='positive_votes', blank=True)
    negative_votes = models.ManyToManyField(User, related_name='negative_votes', blank=True)

    TIME_FRAME = [
        ("seconds", "Seconds"),
        ("minutes", "Minutes"),
        ("hours", "Hours"),
        ("weeks", "Weeks"),
        ("months", "Months"),
        ("years", "Years"),
        ("range", "Range"),
    ]

    test_start_at = models.DateTimeField()
    test_end_at = models.DateTimeField()
    
    time_frame_int = models.IntegerField(default=1)
    time_frame = models.CharField(max_length=8, choices=TIME_FRAME, default="minutes")

    pair = models.CharField(max_length=100, default='')
    broker = models.CharField(max_length=100, default='')
    initial_capital = models.CharField(max_length=100, default='')

    images = GenericRelation(StrategyImages) 
    replies = GenericRelation(Replies) 
    
