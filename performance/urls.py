
from django.urls import path
from .views import *

urlpatterns = [
    path('asset/<str:asset>/<int:perf_id>', get_asset_performance, name='asset_performance'),
    path('strategy/<int:strategy_id>/<int:perf_id>', get_strategy_performance, name='strategy_performance'),
]