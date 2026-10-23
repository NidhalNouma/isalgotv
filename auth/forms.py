import dns.exception
import dns.resolver
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _


def domain_can_receive_email(domain):
    """False only when the domain definitively cannot receive mail.
    DNS timeouts/outages return True so registration is never blocked by them."""
    try:
        dns.resolver.resolve(domain, 'MX', lifetime=3)
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
        return False
    except dns.resolver.NoAnswer:
        # RFC 5321: fall back to the A/AAAA record when there is no MX
        for record_type in ('A', 'AAAA'):
            try:
                dns.resolver.resolve(domain, record_type, lifetime=3)
                return True
            except dns.resolver.NoAnswer:
                continue
            except (dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                return False
            except dns.exception.DNSException:
                return True
        return False
    except dns.exception.DNSException:
        return True

class UserCreationEmailForm(UserCreationForm):
    username = forms.EmailField(required=True, validators=[validate_email])

    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def clean_username(self):
        email = self.cleaned_data['username']
        domain = email.rsplit('@', 1)[-1]
        if not domain_can_receive_email(domain):
            raise forms.ValidationError(
                _("This email domain cannot receive emails. Please check for typos."))
        return email
