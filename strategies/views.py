from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, OuterRef, Subquery
from django.http import Http404
from django.views.decorators.http import require_http_methods

from django_htmx.http import retarget, trigger_client_event, HttpResponseClientRedirect

from .forms import StrategyCommentForm, RepliesForm
from .models import *

def get_strategies(request):
    subscription = request.subscription
    subscription_period_end = request.subscription_period_end
    subscription_plan = request.subscription_plan
    subscription_status = request.subscription_status

    strategies = Strategy.objects.prefetch_related(
            Prefetch('images', queryset=StrategyImages.objects.all())
        )
    
    # print(strategies)

    context =  {'strategies': strategies, 'subscription': subscription, 'subscription_period_end': subscription_period_end, 'subscription_plan': subscription_plan, 'subscription_status': subscription_status}
    return render(request, 'strategies.html', context)

def get_strategy(request, id):
    strategy = {}
    comments = {}
    results = {}
    subscription = request.subscription
    subscription_period_end = request.subscription_period_end
    subscription_plan = request.subscription_plan
    subscription_status = request.subscription_status

    # try:
    #     strategy = get_object_or_404(Strategy, pk=id)
    #     comments = strategy.strategycomments_set.all()
    #     results = strategy.strategyresults_set.all()
    # except Strategy.DoesNotExist:
    #     raise Http404("The object does not exist.")
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
    except Strategy.DoesNotExist:
        raise Http404("The object does not exist.")
    
    context =  {'strategy': strategy, 'results': results, 'comments': comments, 'subscription': subscription, 'subscription_period_end': subscription_period_end, 'subscription_plan': subscription_plan, 'subscription_status': subscription_status}
    return render(request, 'strategy.html', context)

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

            # Trigger an HTMX update to fetch the new comment
            comments = strategy.strategycomments_set.select_related('created_by').prefetch_related(
                'images', Prefetch('replies', queryset=Replies.objects.select_related('created_by').prefetch_related('images')),
            )
            context = {'comments': comments, 'strategy': strategy}
            return render(request, 'include/comments.html', context=context)
        else:
            context = {'errors': form.errors}
            response = render(request, "include/errors.html", context=context)
            return retarget(response, "#add-comment-form-errors")

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

            # Trigger an HTMX update to fetch the new comment
            replies = comment.replies.select_related('created_by').prefetch_related('images')
            context = {'comment': comment, 'replies': replies}
            return render(request, 'include/comment_replies.html', context=context)
        else:
            context = {'errors': form.errors}
            response = render(request, "include/errors.html", context=context)
            return retarget(response, "#add-comment-reply-form-errors-"+str(id))

