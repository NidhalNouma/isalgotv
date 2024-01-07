
from django.contrib import admin
from django.urls import path, include

from .views import *


urlpatterns = [
    path('Introduction/', index, name='docs_index'),
    path('instalation/', instalation, name='docs_instalation'),
    path('setup/', setup, name='docs_setup'),
    path('share/', share, name='docs_share'),
    path('alerts/', alerts, name='docs_alerts'),
    path('automate/', automate, name='docs_automate'),
    path('q&a/', question, name='docs_questions'),
    path('contact_us/', contactus, name='docs_contactus')
]