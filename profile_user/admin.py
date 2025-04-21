from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from .models import User_Profile, Notification

from django.urls import path
from django.template.response import TemplateResponse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings

from django.http import HttpResponseRedirect

from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


 
# Set custom admin display names for User_Profile
User_Profile._meta.verbose_name = "Trader Profile"
User_Profile._meta.verbose_name_plural = "Trader Profiles"

@admin.register(User_Profile)
class UserProfileAdmin(ModelAdmin):

    list_display =  ('user_email', 'has_subscription', 'is_lifetime', 'user_created_at')
    search_fields = ['user__email', 'has_subscription', 'customer_id', 'is_lifetime'] 

    # Custom method to display `user.email`
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'  # Column header in the admin table

    # Custom method to display `user.created_at`
    def user_created_at(self, obj):
        return obj.user.date_joined
    user_created_at.short_description = 'Created At'

@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    pass


def send_html_email(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', 'Newsletter')
        html = request.POST.get('html_content', '')

        recipient_type = request.POST.get('recipient_type', 'all')

        if recipient_type == 'lifetime':
            emails = list(User_Profile.objects.filter(is_lifetime=True).values_list('user__email', flat=True))
        elif recipient_type == 'non_lifetime':
            emails = list(User_Profile.objects.filter(is_lifetime=False).values_list('user__email', flat=True))
        elif recipient_type == 'subscribers':
            emails = list(User_Profile.objects.filter(has_subscription=True).values_list('user__email', flat=True))
        elif recipient_type == 'non_subscribers':
            emails = list(User_Profile.objects.filter(has_subscription=False).values_list('user__email', flat=True))
        else:
            emails = list(User.objects.values_list('email', flat=True))

        
        for email in emails:
            msg = EmailMessage(subject, html, settings.DEFAULT_FROM_EMAIL, [email])
            msg.content_subtype = "html"
            msg.send()
        messages.success(request, "Emails sent to all users")
        return HttpResponseRedirect(request.path)
    context = dict(admin.site.each_context(request))
    return TemplateResponse(request, "admin/send_email.html", context)

# # Insert custom admin URL for sending emails
original_admin_get_urls = admin.site.get_urls

def get_urls():
    custom_urls = [
        path('admin-send-email/', admin.site.admin_view(send_html_email), name='admin_send_email'),
    ]
    return custom_urls + original_admin_get_urls()

admin.site.get_urls = get_urls