from django.urls import path
from .views import *

urlpatterns = [
    # path('home/', home, name='home'),
    path('all/', get_strategies, name='strategies'),
    path('<int:id>/', get_strategy, name='strategy')
]