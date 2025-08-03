# context_processors.py

from django.conf import settings
import json
from django.forms.models import model_to_dict
import environ
import requests

env = environ.Env()

server_ip = requests.get('https://ifconfig.me')


def site_context(request):

    return {
        'server_ip': server_ip.text,
    }