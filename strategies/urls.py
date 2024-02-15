from django.urls import path
from .views import *

urlpatterns = [
    # path('home/', home, name='home'),
    path('all/', get_strategies, name='strategies'),
    path('<int:id>/', get_strategy, name='strategy'),
    path('<int:id>/add_comment', add_comment, name='submit_comment'),
    path('<int:id>/add_result', add_result, name='submit_result'),
    path('<int:id>/add_comment_reply', add_comment_reply, name='submit_comment_reply'),
    path('<int:id>/add_result_reply', add_result_reply, name='submit_result_reply'),
    path('<int:id>/like', strategy_like, name='strategy_like'),
    path('vote/<int:result_id>/<str:vote_type>/', result_vote, name='result_vote'),
    path('like/<int:comment_id>/<str:like_type>/', comment_like, name='comment_like'),
    path('results/', get_results, name='results'),
    path('ideas/', get_ideas, name='ideas'),
]