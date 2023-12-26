
from django.contrib import admin
from django.urls import path, include

from .views import index


urlpatterns = [
    path('', index, name='docs_index'),
    # path('admin/', admin.site.urls),
    # path('accounts/', include('allauth.urls')),
    # path('p/', include('profile_user.urls')),
    # path('st/', include('strategies.urls')) ,
]