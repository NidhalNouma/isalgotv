from django.contrib import admin

from .models import User_Profile, Notification

# Register your models here.

class UserProfileAdmin(admin.ModelAdmin):
    list_display =  ('user_email', 'subscription_id', 'is_lifetime', 'user_created_at')
    search_fields = ['user__email', 'subscription_id', 'customer_id', 'is_lifetime'] 

    # Custom method to display `user.email`
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'  # Column header in the admin table

    # Custom method to display `user.created_at`
    def user_created_at(self, obj):
        return obj.user.date_joined
    user_created_at.short_description = 'Created At'


admin.site.register(User_Profile, UserProfileAdmin)
admin.site.register(Notification)