from django.contrib import admin
from django.contrib.auth.models import User
from strategies.models import Strategy, StrategyPrice, StrategyImages, StrategyComments, StrategyResults, Replies, StrategySubscriber


from unfold.admin import ModelAdmin
from strategies.tasks import send_strategy_email_to_all_users


# Register your models here.
@admin.register(StrategyImages)
class StrategyImagesAdmin(ModelAdmin):
    pass

@admin.register(Replies)
class RepliesAdmin(ModelAdmin):
    pass

@admin.register(StrategyResults)
class StrategyResultsAdmin(ModelAdmin):
    pass

@admin.register(StrategyComments)
class StrategyCommentsAdmin(ModelAdmin):
    pass

@admin.register(Strategy)
class StrategyAdmin(ModelAdmin):
    list_display = ('name', 'premium', 'created_by', 'created_at')
    search_fields = ['name', 'created_by__user__username']
    actions = ['send_new_strategy_email_to_all_users']

    @admin.action(description='Send new strategy email to all users')
    def send_new_strategy_email_to_all_users(self, request, queryset):
        emails = list(User.objects.values_list('email', flat=True))
        for strategy in queryset:
            send_strategy_email_to_all_users(emails, strategy)
        self.message_user(request, f"Emails for {queryset.count()} strategy(ies) have been sent to all users.")

@admin.register(StrategyPrice)
class StrategyPriceAdmin(ModelAdmin):
    list_display = ('strategy', 'amount', 'currency', 'interval', 'interval_count')
    search_fields = ['strategy__name', 'currency']

@admin.register(StrategySubscriber)
class StrategySubscriberAdmin(ModelAdmin):
    list_display = ('strategy', 'user_profile', 'subscription_id', 'created_at')
    search_fields = ['strategy__name', 'user_profile__user__username', 'subscription_id']