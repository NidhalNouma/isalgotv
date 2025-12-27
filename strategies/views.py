from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, OuterRef, Subquery
from django.http import Http404, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django_htmx.http import retarget, trigger_client_event, HttpResponseClientRedirect

from .forms import StrategyCommentForm, RepliesForm, StrategyResultForm
from .models import *
from automate.models import StrategyPerformance, TradeDetails
from automate.functions.performance import get_strategy_performance_data, get_days_performance, get_overview_performance_data, get_asset_performance_data

from profile_user.utils.notifcations import send_notification

from django.db.models.functions import Random
from django.db.models import Q

def get_strategies(request):
    filter = Q(is_live=True, premium__in=['Free', 'Beta', 'Premium'])
    
    if request.user.is_authenticated: 
        filter = Q(is_live=True, premium__in=['Free', 'Beta', 'Premium']) | Q(is_live=True, premium='VIP', created_by=request.user)

    superuser = request.user.is_superuser if request.user.is_authenticated else False
    if superuser:
        filter = Q()
    
    strategies = Strategy.objects.prefetch_related(
        Prefetch('images', queryset=StrategyImages.objects.all())
    ).filter(filter)
    
    # print(strategies)

    context =  {'strategies': strategies, 'show_banner': True}
    return render(request, 'strategies.html', context)

def get_reports(request):

    filter = {
        "strategy__is_live": True,
        "strategy__premium__in": ['Free', 'Beta', 'Premium'] 
    }

    superuser = request.user.is_superuser if request.user.is_authenticated else False
    if superuser:
        filter = {}

    pair_name = request.GET.get('pair')

    unique_pairs = StrategyResults.objects.filter(**filter).values_list('pair', flat=True).distinct()
    unique_pairs_list = unique_pairs


    if pair_name:
        results = StrategyResults.objects.filter(pair=pair_name, **filter).order_by('-created_at')
    else:
        results = StrategyResults.objects.filter(**filter).order_by('-created_at')
    
    # print(strategies)

    context =  {'show_banner': True, 'results': results, 'pairs': unique_pairs_list, 'selected_pair': pair_name}
    return render(request, 'results.html', context)

def get_ideas(request):

    filter = {
        "strategy__is_live": True,
        "strategy__premium__in": ['Free', 'Beta', 'Premium'] 
    }

    superuser = request.user.is_superuser if request.user.is_authenticated else False
    if superuser:
        filter = {}

    ideas = StrategyComments.objects.filter(**filter).order_by('-created_at')
    context =  {'ideas': ideas }
    return render(request, 'ideas.html', context)

def get_strategy(request, slug):
    try:
        strategy = Strategy.objects.select_related('created_by').prefetch_related(
                'images',
            ).get(slug=slug)
        
        if not strategy.is_live and (not request.user.is_authenticated or not request.user.is_superuser):
            raise Http404("The object does not exist.")

        comments = strategy.strategycomments_set.select_related('created_by').prefetch_related(
                'images', Prefetch('replies', queryset=Replies.objects.select_related('created_by').prefetch_related('images')),
            )
        
        results = strategy.strategyresults_set.select_related('created_by').prefetch_related(
                'images', Prefetch('replies', queryset=Replies.objects.select_related('created_by').prefetch_related('images')),
            )

        strategy_performances = StrategyPerformance.objects.filter(strategy=strategy).first()

        overview_performance = get_overview_performance_data(strategy_performances)
        chart_performance = get_days_performance(strategy_performances)
        # asset_performance = get_asset_performance_data(strategy_performances)
        trades = TradeDetails.objects.filter(
            strategy=strategy,
            status__in=['C'] 
        ).order_by('-exit_time')[:20]



        # random_results = StrategyResults.objects.annotate(random_number=Random()).order_by('-profit_factor', 'random_number')[:10]

        context =  {
            'strategy': strategy, 
            'results': results, 
            'comments': comments, 
            # 'random_results': results, 
            'overview_data': overview_performance, 
            'chart_data': chart_performance,
            'trades': trades,
            'next_start': trades.count(),
            'only_closed_trades': True,
        }
        return render(request, 'strategy.html', context)
    
    except Strategy.DoesNotExist:
        raise Http404("The object does not exist.")
    

def get_strategy_id(request, id):
    
    try:
        strategy = Strategy.objects.get(id=id)
        return HttpResponseRedirect(reverse('strategy', args=[strategy.slug]))
        
    except Strategy.DoesNotExist:
        raise Http404("The object does not exist.")


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
def add_report(request, id):
    strategy = Strategy.objects.get(pk=id)

    if request.method == 'POST':
        try:

            settings_data = {}
            for key, value_list in request.POST.items():
                if key.startswith('settings_'):
                    setting_name = key[len('settings_'):]
                    settings_data[setting_name] = value_list[0:] 

            settings = strategy.settings
            for item in settings:
                group_key = item['key']
                group_value = item['value']
                for lines in group_value:
                    for set in lines:
                        setting_name = set['name']
                        if setting_name in settings_data:
                            set['default_value'] = settings_data[setting_name]
                        elif set['type'] == 'boolean':
                            if setting_name not in settings_data:
                                set['default_value'] = 'false'


            performance_data = {}
            for key, value in request.POST.items():
                if key.startswith("performance_"):
                    # Remove "performance_" prefix from the key
                    performance_key = key[len("performance_"):]
                    # print('performance_key', performance_key)
                    performance_data[performance_key] = value

            if not request.POST.get('list_of_trades'):
                raise ValueError("List of trades was not found.")
            
            form_data = {
                'pair': request.POST.get('performance_pair'),
                'broker': request.POST.get('performance_broker'),
                'initial_capital': request.POST.get('performance_initial_capital'),

                'test_start_at': request.POST.get('performance_start_at'),
                'test_end_at': request.POST.get('performance_end_at'),
                'time_frame_int': request.POST.get('performance_time_frame_int'),
                'time_frame': request.POST.get('performance_time_frame'),

                'settings': settings,
                'performance': performance_data,
                'description': request.POST.get('description'),

                'list_of_trades': request.POST.get('list_of_trades'),
            }
            # print(request.POST)
            form = StrategyResultForm(form_data, request.FILES)  # Allow file uploads
            if form.is_valid():
                result = form.save(commit=False)
                result.strategy = strategy
                result.version = strategy.version
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
        
        except Exception as e:
            error_message = e.messages[0] if isinstance(e.messages, list) else "An error occurred while adding the result." #str(e)

            context = {'errors': error_message}
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

            send_notification(request.user.user_profile, comment.created_by, html_text, f"/strategies/{comment.strategy.slug}/?comment={comment.id}")

            # Trigger an HTMX update to fetch the new comment
            replies = comment.replies.select_related('created_by').prefetch_related('images')
            context = {'comment': comment, 'replies': replies}
            return render(request, 'include/comment_replies.html', context=context)
        else:
            context = {'errors': form.errors}
            response = render(request, "include/st_post_errors.html", context=context)
            return retarget(response, "#reply-form-errors-"+str(id)+"-comment")

@require_http_methods([ "POST"])
def add_report_reply(request, id):
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

            send_notification(request.user.user_profile, result.created_by, html_text, f"/strategies/{result.strategy.slug}/?result={result.id}")

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

        send_notification(request.user.user_profile, result.created_by, html_text, f"/strategies/{result.strategy.slug}/?result={result.id}")

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

                send_notification(request.user.user_profile, comment.created_by, html_text, f"/strategies/{comment.strategy.slug}/?comment={comment.id}")

        elif like_type == 'negative':
            if request.user in comment.dislike.all():
                comment.dislike.remove(request.user)
            else:
                comment.dislike.add(request.user)
                comment.likes.remove(request.user)

                tv_username = request.user.user_profile.tradingview_username if request.user.user_profile.tradingview_username else 'Someone'
                html_text = f"<span class='font-semibold'>{tv_username}</span>'s disliked your comment."

                send_notification(request.user.user_profile, comment.created_by, html_text, f"/strategies/{comment.strategy.slug}/?comment={comment.id}")

    context = {'comment': comment}
    return render(request, 'include/comment_likes.html', context=context)