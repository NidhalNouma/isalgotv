from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from .models import User_Profile, Notification
from strategies.models import Strategy
from strategies.tasks import send_strategy_email_to_all_users

from django.urls import path
from django.template.response import TemplateResponse
from django.contrib import messages
from django.core.mail import EmailMessage, get_connection
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
        header = request.POST.get('header', '')
        subject = request.POST.get('subject', '')
        html = request.POST.get('html_content', '')

        if not subject.strip() or not html.strip():
            messages.error(request, "Both subject and HTML content are required.")
            return HttpResponseRedirect(request.path)
        
        # Ensure HTML content has at least 300 characters
        if len(html) < 300:
            messages.error(request, "HTML content must be at least 300 characters long.")
            return HttpResponseRedirect(request.path)

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

                
        if header:
            from_email = f"IsAlgo - {header} <{settings.EMAIL_HOST_USER}>"
        else:
            from_email = f"IsAlgo <{settings.EMAIL_HOST_USER}>"

        # Open one connection
        connection = get_connection()

        # Build all messages
        emails_messages = []
        for recipient in emails:
            msg = EmailMessage(
                subject=subject,
                body=html,
                from_email=from_email,
                to=[recipient],
                connection=connection
            )
            msg.content_subtype = "html"
            emails_messages.append(msg)

        # Send them all in one go (over the same connection)
        connection.send_messages(emails_messages)

        messages.success(request, "Emails sent succesfully")
        return HttpResponseRedirect(request.path)
    
    context = dict(admin.site.each_context(request))
    return TemplateResponse(request, "admin/send_email.html", context)

def send_strategy_html_email(request):
    if request.method == 'POST':
        header = request.POST.get('header', '')
        subject = request.POST.get('subject', '')
        html = request.POST.get('html_content', '')


        strategy_id = request.POST.get('strategy', '')

        if not strategy_id:
            messages.error(request, "Strategy must be provided.")
            return HttpResponseRedirect(request.path)
        
        strategy = Strategy.objects.get(id = strategy_id)

        
        # Ensure HTML content has at least 300 characters
        if len(html) > 0 and len(html) < 300:
            messages.error(request, "HTML content must be at least 300 characters long.")
            return HttpResponseRedirect(request.path)

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

        
        send_strategy_email_to_all_users(emails, strategy, header, subject, html)

        messages.success(request, "Emails sent succesfully")
        return HttpResponseRedirect(request.path)
    
    context = dict(admin.site.each_context(request))
    context['strategies'] = Strategy.objects.all()
    return TemplateResponse(request, "admin/send_strategy_email.html", context)



# # Insert custom admin URL for sending emails
original_admin_get_urls = admin.site.get_urls

def get_urls():
    custom_urls = [
        path('admin-send-email/', admin.site.admin_view(send_html_email), name='admin_send_email'),
        path('admin-send-strategy-email/', admin.site.admin_view(send_strategy_html_email), name='admin_send_strategy_email'),
    ]
    return custom_urls + original_admin_get_urls()

admin.site.get_urls = get_urls