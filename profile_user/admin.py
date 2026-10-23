from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import User, Group

from .models import User_Profile, Notification
from strategies.models import Strategy
from strategies.tasks import send_strategy_email_to_all_users
from profile_user.utils.stripe import delete_seller_account as stripe_delete_seller_account

from django.urls import path
from django.template.response import TemplateResponse
from django.contrib import messages
from django.core.mail import EmailMessage, get_connection
from django.conf import settings

from django.http import HttpResponseRedirect

import re
import json

from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm


admin.site.unregister(User)
admin.site.unregister(Group)


def _parse_recipient_tokens(raw_value):
    if not raw_value:
        return []
    return [token.strip() for token in re.split(r'[\n,;]+', raw_value) if token.strip()]


def _resolve_recipient_emails(recipient_type, specific_recipients_raw=''):
    if recipient_type == 'all':
        return list(
            User.objects.exclude(email__isnull=True)
            .exclude(email='')
            .values_list('email', flat=True)
        ), []

    if recipient_type != 'specific':
        return [], [f"Unsupported recipient type: {recipient_type}"]

    tokens = _parse_recipient_tokens(specific_recipients_raw)
    if not tokens:
        return [], ['Please provide at least one user email or username.']

    email_tokens = {t.lower() for t in tokens if '@' in t}
    username_tokens = {t for t in tokens if '@' not in t}

    resolved_emails = set()
    resolved_emails.update(
        User.objects.filter(email__in=email_tokens)
        .exclude(email__isnull=True)
        .exclude(email='')
        .values_list('email', flat=True)
    )

    resolved_username_rows = User.objects.filter(username__in=username_tokens).values_list('username', 'email')
    found_usernames = set()
    for username, email in resolved_username_rows:
        found_usernames.add(username)
        if email:
            resolved_emails.add(email)

    resolved_email_lc = {email.lower() for email in resolved_emails}
    missing_emails = sorted(email_tokens - resolved_email_lc)
    missing_usernames = sorted(username_tokens - found_usernames)
    unresolved = missing_emails + missing_usernames

    return sorted(resolved_emails), unresolved


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

    list_display =  ('user_email', 'seller_status', 'email_verified', 'user_created_at')
    search_fields = ['user__email', 'customer_id'] 
    actions = ['create_seller_account']

    # Custom method to display `user.email`
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'  # Column header in the admin table

    # Custom method to display `user.created_at`
    def user_created_at(self, obj):
        return obj.user.date_joined
    user_created_at.short_description = 'Created At'

    def seller_status(self, obj):
        if obj.seller_account_verified:
            return 'Verified'
        elif obj.seller_account_id:
            return 'Pending'
        return '—'
    seller_status.short_description = 'Seller'

    def email_verified(self, obj):
        return obj.email_verified
    email_verified.short_description = 'Email Verified'

    @admin.action(description='Create seller account')
    def create_seller_account(self, request, queryset):
        created = 0
        skipped = 0
        errors = []
        for profile in queryset:
            if profile.seller_account_id:
                skipped += 1
                continue
            try:
                profile.get_seller_account_id()
                created += 1
            except Exception as e:
                errors.append(f'{profile.user.email}: {e}')

        if created:
            messages.success(request, f'Created seller account for {created} user(s).')
        if skipped:
            messages.info(request, f'Skipped {skipped} user(s) — already have a seller account.')
        for err in errors:
            messages.error(request, f'Error: {err}')

@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    pass


def send_html_email(request):
    if request.method == 'POST':
        header = request.POST.get('header', '')
        subject = request.POST.get('subject', '')
        html = request.POST.get('html_content', '')
        recipient_type = request.POST.get('recipient_type', 'all')
        specific_recipients = request.POST.get('specific_recipients', '')

        if not subject.strip() or not html.strip():
            messages.error(request, "Both subject and HTML content are required.")
            return HttpResponseRedirect(request.path)
        
        # Ensure HTML content has at least 300 characters
        if len(html) < 300:
            messages.error(request, "HTML content must be at least 300 characters long.")
            return HttpResponseRedirect(request.path)

        emails, unresolved = _resolve_recipient_emails(recipient_type, specific_recipients)
        if unresolved:
            messages.error(
                request,
                "Some users could not be resolved: " + ", ".join(unresolved[:15])
                + ("..." if len(unresolved) > 15 else "")
            )
            return HttpResponseRedirect(request.path)

        if not emails:
            messages.warning(request, "No recipients found.")
            return HttpResponseRedirect(request.path)

                
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
        specific_recipients = request.POST.get('specific_recipients', '')
        emails, unresolved = _resolve_recipient_emails(recipient_type, specific_recipients)
        if unresolved:
            messages.error(
                request,
                "Some users could not be resolved: " + ", ".join(unresolved[:15])
                + ("..." if len(unresolved) > 15 else "")
            )
            return HttpResponseRedirect(request.path)

        if not emails:
            messages.warning(request, "No recipients found.")
            return HttpResponseRedirect(request.path)

        
        send_strategy_email_to_all_users(emails, strategy, header, subject, html)

        messages.success(request, "Emails sent succesfully")
        return HttpResponseRedirect(request.path)
    
    context = dict(admin.site.each_context(request))
    context['strategies'] = Strategy.objects.all()
    return TemplateResponse(request, "admin/send_strategy_email.html", context)



def delete_seller_account_view(request):
    if request.method == 'POST':
        account_id = request.POST.get('seller_account_id', '').strip()

        if not account_id:
            messages.error(request, "Seller account ID is required.")
            return HttpResponseRedirect(request.path)

        # Find the matching user profile
        try:
            profile = User_Profile.objects.get(seller_account_id=account_id)
        except User_Profile.DoesNotExist:
            profile = None

        # Delete from Stripe
        try:
            stripe_delete_seller_account(account_id)
        except Exception as e:
            messages.error(request, f"Stripe error: {e}")
            return HttpResponseRedirect(request.path)

        # Clear the profile fields
        if profile:
            profile.seller_account_id = ''
            profile.seller_account_verified = False
            profile.save(update_fields=["seller_account_id", "seller_account_verified"])
            messages.success(request, f"Seller account {account_id} deleted and profile for {profile.user.email} cleared.")
        else:
            messages.warning(request, f"Seller account {account_id} deleted from Stripe, but no matching user profile was found.")

        return HttpResponseRedirect(request.path)

    context = dict(admin.site.each_context(request))
    return TemplateResponse(request, "admin/delete_seller_account.html", context)


def send_marketing_email_view(request):
    if request.method == 'POST':
        is_preview = request.POST.get('preview') == '1'
        subject = request.POST.get('subject', '').strip()
        preheader = request.POST.get('preheader', '').strip()
        recipient_type = request.POST.get('recipient_type', 'all')
        specific_recipients = request.POST.get('specific_recipients', '')

        # Parse sections from form fields like sections[0][title], sections[0][images][0][src], etc.
        sections = {}
        flat_pattern = re.compile(r'^sections\[(\d+)\]\[(?!images\])(.+)\]$')
        img_pattern = re.compile(r'^sections\[(\d+)\]\[images\]\[(\d+)\]\[(.+)\]$')
        for key, value in request.POST.items():
            m = flat_pattern.match(key)
            if m:
                idx = int(m.group(1))
                field = m.group(2)
                if idx not in sections:
                    sections[idx] = {}
                if value.strip():
                    sections[idx][field] = value.strip()
                continue
            m = img_pattern.match(key)
            if m:
                idx = int(m.group(1))
                img_idx = int(m.group(2))
                field = m.group(3)
                if idx not in sections:
                    sections[idx] = {}
                if 'images' not in sections[idx]:
                    sections[idx]['images'] = {}
                if img_idx not in sections[idx]['images']:
                    sections[idx]['images'][img_idx] = {}
                if value.strip():
                    sections[idx]['images'][img_idx][field] = value.strip()

        # Convert images dicts to ordered lists and build image_rows
        for idx in sections:
            if 'images' in sections[idx]:
                img_dict = sections[idx]['images']
                images_list = [img_dict[k] for k in sorted(img_dict.keys()) if img_dict[k].get('src')]
                if images_list:
                    per_row = int(sections[idx].get('images_per_row', 1))
                    sections[idx]['images'] = images_list
                    sections[idx]['image_col_width'] = str(int(100 / per_row))
                    # Chunk images into rows of `per_row`
                    sections[idx]['image_rows'] = [
                        images_list[i:i + per_row] for i in range(0, len(images_list), per_row)
                    ]
                else:
                    del sections[idx]['images']

        # Convert to ordered list
        sections_list = [sections[k] for k in sorted(sections.keys()) if sections[k]]

        if not subject:
            messages.error(request, 'Subject is required.')
            return HttpResponseRedirect(request.path)

        if not sections_list:
            messages.error(request, 'At least one section with content is required.')
            return HttpResponseRedirect(request.path)

        if is_preview:
            from profile_user.utils.send_mails import email_context
            from django.template.loader import render_to_string
            context = {
                'sections': sections_list,
                'email_subject': subject,
                'preheader': preheader,
                **email_context(),
            }
            html = render_to_string('emails/marketing_email.html', context=context)
            from django.http import HttpResponse
            return HttpResponse(html)

        emails, unresolved = _resolve_recipient_emails(recipient_type, specific_recipients)
        if unresolved:
            messages.error(
                request,
                'Some users could not be resolved: ' + ', '.join(unresolved[:15])
                + ('...' if len(unresolved) > 15 else '')
            )
            return HttpResponseRedirect(request.path)

        if not emails:
            messages.warning(request, 'No recipients found for the selected group.')
            return HttpResponseRedirect(request.path)

        from profile_user.utils.send_mails import send_marketing_email
        send_marketing_email(
            recipients=emails,
            subject=subject,
            sections=sections_list,
            preheader=preheader,
        )

        messages.success(request, f'Marketing email sent to {len(emails)} recipient(s).')
        return HttpResponseRedirect(request.path)

    context = dict(admin.site.each_context(request))
    return TemplateResponse(request, 'admin/send_marketing_email.html', context)


# # Insert custom admin URL for sending emails
original_admin_get_urls = admin.site.get_urls

def get_urls():
    custom_urls = [
        path('admin-send-email/', admin.site.admin_view(send_html_email), name='admin_send_email'),
        path('admin-send-strategy-email/', admin.site.admin_view(send_strategy_html_email), name='admin_send_strategy_email'),
        path('admin-send-marketing-email/', admin.site.admin_view(send_marketing_email_view), name='admin_send_marketing_email'),
        path('admin-delete-seller-account/', admin.site.admin_view(delete_seller_account_view), name='admin_delete_seller_account'),
    ]
    return custom_urls + original_admin_get_urls()

admin.site.get_urls = get_urls