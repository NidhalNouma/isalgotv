from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, OuterRef, Subquery
from django.http import Http404
from django.views.decorators.http import require_http_methods

from django_htmx.http import retarget, trigger_client_event, HttpResponseClientRedirect

from .forms import StrategyCommentForm, RepliesForm, StrategyResultForm
from .models import *

from profile_user.utils.notifcations import send_notification

from django.db.models.functions import Random
from django.db.models import F

def get_strategies(request):
    strategies = Strategy.objects.prefetch_related(
            Prefetch('images', queryset=StrategyImages.objects.all())
        )
    
    # print(strategies)

    context =  {'strategies': strategies}
    return render(request, 'strategies.html', context)

def get_results(request):
    pair_name = request.GET.get('pair')

    unique_pairs = StrategyResults.objects.values_list('pair', flat=True).distinct()
    unique_pairs_list = unique_pairs


    if pair_name:
        results = StrategyResults.objects.filter(pair=pair_name).order_by('-created_at')
    else:
        results = StrategyResults.objects.all().order_by('-created_at')
    
    # print(strategies)

    context =  {'results': results, 'pairs': unique_pairs_list, 'selected_pair': pair_name}
    return render(request, 'results.html', context)

def get_ideas(request):
    ideas = StrategyComments.objects.all().order_by('-created_at')
    context =  {'ideas': ideas }
    return render(request, 'ideas.html', context)

def get_strategy(request, id):
    strategy = {}
    comments = {}
    results = {}
    
    try:
        strategy = Strategy.objects.select_related('created_by').prefetch_related(
                'images',
            ).get(pk=id)

        comments = strategy.strategycomments_set.select_related('created_by').prefetch_related(
                'images', Prefetch('replies', queryset=Replies.objects.select_related('created_by').prefetch_related('images')),
            )
        
        results = strategy.strategyresults_set.select_related('created_by').prefetch_related(
                'images', Prefetch('replies', queryset=Replies.objects.select_related('created_by').prefetch_related('images')),
            )

        Strategy.objects.filter(pk=id).update(view_count=F('view_count') + 1)
        
        random_results = StrategyResults.objects.annotate(random_number=Random()).order_by('-profit_factor', 'random_number')[:10]
    except Strategy.DoesNotExist:
        raise Http404("The object does not exist.")
    
    context =  {'strategy': strategy, 'results': results, 'comments': comments, 'random_results': random_results}
    return render(request, 'strategy.html', context)


def strategy_like(request, id):
    strategy = Strategy.objects.get(pk=id)

    if request.user:
        if request.user in strategy.likes.all():
            strategy.likes.remove(request.user)
        else:
            strategy.likes.add(request.user)

    context = {'strategy': strategy}
    return render(request, 'include/likes_results_comments.html', context=context)

@require_http_methods([ "POST"])
def add_comment(request, id):
    strategy = Strategy.objects.get(pk=id)

    if request.method == 'POST':
        form_data = {
            'description': request.POST.get('description'),
            # Add other form fields here
        }
        form = StrategyCommentForm(form_data, request.FILES)  # Allow file uploads
        if form.is_valid():
            comment = form.save(commit=False)
            comment.strategy = strategy
            comment.created_by = request.user.user_profile
            comment.save()

            # Save images with modified name and URL
            for index, image in enumerate(request.FILES.getlist('images')):
                image_name = f'{comment.id}_{index}_{image.name}'  
                StrategyImages.objects.create(
                    name=image_name,
                    img=image,
                    content_object=comment,
                )
            print(form_data)    

            # Trigger an HTMX update to fetch the new comment
            comments = strategy.strategycomments_set.select_related('created_by').prefetch_related(
                'images', Prefetch('replies', queryset=Replies.objects.select_related('created_by').prefetch_related('images')),
            )
            context = {'comments': comments, 'strategy': strategy}
            return render(request, 'include/comments.html', context=context)
        else:
            context = {'errors': form.errors}
            print(context)
            response = render(request, "include/st_post_errors.html", context=context)
            return retarget(response, "#add-comment-form-errors")

@require_http_methods([ "POST"])
def add_result(request, id):
    strategy = Strategy.objects.get(pk=id)

    if request.method == 'POST':

        settings_data = {}
        for key, value_list in request.POST.items():
            if key.startswith('settings_'):
                setting_name = key[len('settings_'):]
                settings_data[setting_name] = value_list[0:] 

        settings = strategy.settings

        # for setting in settings['objects']:
        #     setting_name = setting['name']
        #     if setting_name in settings_data:
        #         setting['default_value'] = settings_data[setting_name]

        for group_key, group_value in settings.items():
            for lines in group_value:
                for set in lines:
                    setting_name = set['name']
                    if setting_name in settings_data:
                        set['default_value'] = settings_data[setting_name]
                    elif set['type'] == 'boolean':
                        if setting_name not in settings_data:
                            set['default_value'] = 'false'

        # print(settings_data)
        print(settings)
        # return

        form_data = {
            'description': request.POST.get('description'),
            'pair': request.POST.get('pair'),
            'broker': request.POST.get('broker'),
            'initial_capital': request.POST.get('initial_capital'),

            'total_trade': request.POST.get('total_trades'),
            'total_trade_long': request.POST.get('total_trades_long'),
            'total_trade_short': request.POST.get('total_trades_short'),

            'winning_total_trade': request.POST.get('winning_trades'),
            'winning_total_trade_long': request.POST.get('winning_trades_long'),
            'winning_total_trade_short': request.POST.get('winning_trades_short'),

            'losing_total_trade': request.POST.get('losing_trades'),
            'losing_total_trade_long': request.POST.get('losing_trades_long'),
            'losing_total_trade_short': request.POST.get('losing_trades_short'),

            'net_profit': request.POST.get('net_profit'),
            'net_profit_long': request.POST.get('net_profit_long'),
            'net_profit_short': request.POST.get('net_profit_short'),

            'net_profit_percentage': request.POST.get('net_profit_percentage'),
            'net_profit_percentage_long': request.POST.get('net_profit_percentage_long'),
            'net_profit_percentage_short': request.POST.get('net_profit_percentage_short'),

            'max_drawdown': request.POST.get('max_dd'),
            'max_drawdown_percentage': request.POST.get('max_dd_percentage'),

            'profit_factor': request.POST.get('profit_factor'),
            'profit_factor_long': request.POST.get('profit_factor_long'),
            'profit_factor_short': request.POST.get('profit_factor_short'),

            'profitable_percentage': request.POST.get('profitable_percentage'),
            'profitable_percentage_long': request.POST.get('profitable_percentage_long'),
            'profitable_percentage_short': request.POST.get('profitable_percentage_short'),

            'gross_profit': request.POST.get('gross_profit'),
            'gross_profit_long': request.POST.get('gross_profit_long'),
            'gross_profit_short': request.POST.get('gross_profit_short'),

            'gross_profit_percentage': request.POST.get('gross_profit_percent'),
            'gross_profit_percentage_long': request.POST.get('gross_profit_percent_long'),
            'gross_profit_percentage_short': request.POST.get('gross_profit_percent_short'),

            'gross_loss': request.POST.get('gross_loss'),
            'gross_loss_long': request.POST.get('gross_loss_long'),
            'gross_loss_short': request.POST.get('gross_loss_short'),

            'gross_loss_percentage': request.POST.get('gross_loss_percent'),
            'gross_loss_percentage_long': request.POST.get('gross_loss_percent_long'),
            'gross_loss_percentage_short': request.POST.get('gross_loss_percent_short'),

            'test_start_at': request.POST.get('start_at'),
            'test_end_at': request.POST.get('end_at'),
            'time_frame_int': request.POST.get('time_frame'),
            'time_frame': request.POST.get('time_frame_period'),
            'settings': settings,
        }
        print(request.POST)
        form = StrategyResultForm(form_data, request.FILES)  # Allow file uploads
        if form.is_valid():
            result = form.save(commit=False)
            result.strategy = strategy
            result.created_by = request.user.user_profile
            result.save()


            # Save images with modified name and URL
            for index, image in enumerate(request.FILES.getlist('images')):
                image_name = f'{result.id}_{index}_{image.name}'  
                StrategyImages.objects.create(
                    name=image_name,
                    img=image,
                    content_object=result,
                )

            # Trigger an HTMX update to fetch the new comment
            results = strategy.strategyresults_set.select_related('created_by').prefetch_related(
                'images', Prefetch('replies', queryset=Replies.objects.select_related('created_by').prefetch_related('images')),
            )
            context = {'results': results, 'strategy': strategy}
            response = render(request, 'include/results.html', context=context)
            return response
        else:
            print(form.errors)
            context = {'errors': form.errors}
            response = render(request, "include/st_post_errors.html", context=context)
            return retarget(response, "#add-result-form-errors")

@require_http_methods([ "POST"])
def add_comment_reply(request, id):
    comment = StrategyComments.objects.get(pk=id)

    if request.method == 'POST':
        form_data = {
            'description': request.POST.get('description'),
            # Add other form fields here
        }
        form = RepliesForm(form_data, request.FILES)  # Allow file uploads
        if form.is_valid():
            reply = form.save(commit=False)
            reply.content_object = comment
            reply.created_by = request.user.user_profile
            reply.save()

            # Save images with modified name and URL
            for index, image in enumerate(request.FILES.getlist('images')):
                image_name = f'{comment.id}_{reply.id}_{index}_{image.name}'  
                StrategyImages.objects.create(
                    name=image_name,
                    img=image,
                    content_object=reply,
                )

            tv_username = request.user.user_profile.tradingview_username if request.user.user_profile.tradingview_username else 'Someone'
            html_text = f"<span class='font-semibold'>{tv_username}</span>'s replied to your idea. </br></br>{reply.description}"

            send_notification(request.user.user_profile, comment.created_by, html_text, f"/st/{comment.strategy.id}/?comment={comment.id}")

            # Trigger an HTMX update to fetch the new comment
            replies = comment.replies.select_related('created_by').prefetch_related('images')
            context = {'comment': comment, 'replies': replies}
            return render(request, 'include/comment_replies.html', context=context)
        else:
            context = {'errors': form.errors}
            response = render(request, "include/st_post_errors.html", context=context)
            return retarget(response, "#reply-form-errors-"+str(id)+"-comment")

@require_http_methods([ "POST"])
def add_result_reply(request, id):
    result = StrategyResults.objects.get(pk=id)

    if request.method == 'POST':
        form_data = {
            'description': request.POST.get('description'),
            # Add other form fields here
        }
        form = RepliesForm(form_data, request.FILES)  # Allow file uploads
        if form.is_valid():
            reply = form.save(commit=False)
            reply.content_object = result
            reply.created_by = request.user.user_profile
            reply.save()

            # Save images with modified name and URL
            for index, image in enumerate(request.FILES.getlist('images')):
                image_name = f'{result.id}_{reply.id}_{index}_{image.name}'  
                StrategyImages.objects.create(
                    name=image_name,
                    img=image,
                    content_object=reply,
                )

            

            tv_username = request.user.user_profile.tradingview_username if request.user.user_profile.tradingview_username else 'Someone'
            html_text = f"<span class='font-semibold'>{tv_username}</span>'s replied to your result. </br></br>{reply.description}"

            send_notification(request.user.user_profile, result.created_by, html_text, f"/st/{result.strategy.id}/?result={result.id}")

            # Trigger an HTMX update to fetch the new comment
            replies = result.replies.select_related('created_by').prefetch_related('images')
            context = {'result': result, 'replies': replies}
            return render(request, 'include/result_replies.html', context=context)
        else:
            context = {'errors': form.errors}
            response = render(request, "include/st_post_errors.html", context=context)
            return retarget(response, "#reply-form-errors-"+str(id)+"-result")

def result_vote(request, result_id, vote_type):
    result = get_object_or_404(StrategyResults, pk=result_id)

    if request.user:
        if vote_type == 'positive':
            if request.user in result.positive_votes.all():
                result.positive_votes.remove(request.user)

            else:
                result.positive_votes.add(request.user)
                result.negative_votes.remove(request.user)
        elif vote_type == 'negative':
            if request.user in result.negative_votes.all():
                result.negative_votes.remove(request.user)
            else:
                result.negative_votes.add(request.user)
                result.positive_votes.remove(request.user)
        

        tv_username = request.user.user_profile.tradingview_username if request.user.user_profile.tradingview_username else 'Someone'
        html_text = f"<span class='font-semibold'>{tv_username}</span>'s voted one your result."

        send_notification(request.user.user_profile, result.created_by, html_text, f"/st/{result.strategy.id}/?result={result.id}")

    context = {'result': result}
    return render(request, 'include/result_votes.html', context=context)

def comment_like(request, comment_id, like_type):
    comment = get_object_or_404(StrategyComments, pk=comment_id)

    if request.user:
        if like_type == 'positive':
            if request.user in comment.likes.all():
                comment.likes.remove(request.user)
            else:
                comment.likes.add(request.user)
                comment.dislike.remove(request.user)

                tv_username = request.user.user_profile.tradingview_username if request.user.user_profile.tradingview_username else 'Someone'
                html_text = f"<span class='font-semibold'>{tv_username}</span>'s liked your comment."

                send_notification(request.user.user_profile, comment.created_by, html_text, f"/st/{comment.strategy.id}/?comment={comment.id}")

        elif like_type == 'negative':
            if request.user in comment.dislike.all():
                comment.dislike.remove(request.user)
            else:
                comment.dislike.add(request.user)
                comment.likes.remove(request.user)

                tv_username = request.user.user_profile.tradingview_username if request.user.user_profile.tradingview_username else 'Someone'
                html_text = f"<span class='font-semibold'>{tv_username}</span>'s disliked your comment."

                send_notification(request.user.user_profile, comment.created_by, html_text, f"/st/{comment.strategy.id}/?comment={comment.id}")

    context = {'comment': comment}
    return render(request, 'include/comment_likes.html', context=context)