from django.urls import path
from .views import *

urlpatterns = [
    # path('home/', home, name='home'),
    path('', get_strategies, name='strategies'),
    path('<int:id>/add_comment', add_comment, name='submit_comment'),
    path('<int:id>/add_report', add_report, name='submit_report'),
    path('<int:id>/add_comment_reply', add_comment_reply, name='submit_comment_reply'),
    path('<int:id>/add_report_reply', add_report_reply, name='submit_report_reply'),
    path('<int:id>/like', strategy_like, name='strategy_like'),
    path('vote/<int:result_id>/<str:vote_type>/', result_vote, name='result_vote'),
    path('like/<int:comment_id>/<str:like_type>/', comment_like, name='comment_like'),
    path('reports/', get_reports, name='reports'),
    path('ideas/', get_ideas, name='ideas'),
    path('<slug:slug>/', get_strategy, name='strategy'),
    path('id/<int:id>/', get_strategy_id, name='strategy_id'),
]