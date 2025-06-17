
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRedirect, retarget

from .functions.ai import get_ai_response, get_system_content

from asgiref.sync import sync_to_async
import environ

import json
import stripe

env = environ.Env()
stripe.api_key = env('STRIPE_API_KEY')

# Create your views here.
def index(request):
    return render(request, "saro/index.html")

def get_ai_system_content(request):
    if request.method == "POST":
        if request.user.is_authenticated and request.user.is_superuser:
            system_content = get_system_content()
            context = {
                "system_content": system_content,
            }

            response = render(request, 'include/settings/ai_system_content.html', context)
            return response

@sync_to_async
def update_user_tokens(user_profile, total_tokens, daily_token_remaining, daily_token):
    """ Update user AI token usage safely in async context. """
    tokens = total_tokens - daily_token_remaining
     
    print("Total Tokens: ", total_tokens, "Daily Token Remaining: ", daily_token_remaining, "Tokens: ", tokens) 

    if tokens > 0:
        new_available_tokens = user_profile.ai_tokens_available - tokens
        if new_available_tokens < 0:
            new_available_tokens = 0
        user_profile.ai_tokens_available = new_available_tokens
        user_profile.ai_tokens_used_today = daily_token
    else:
        user_profile.ai_tokens_used_today += total_tokens

    user_profile.save()  # ORM operation inside sync_to_async


async def ai_chat_view(request):
    if request.method == "POST":
        try:
            daily_token = 50000
            if request.has_subscription:
                daily_token = 500000
            
            data = json.loads(request.body)
            user_message = data.get("userMessage", "").strip()
            messages = data.get("messages", [])

            user_profile = request.user_profile
            if not user_profile:
                return JsonResponse({"error": "User not found"}, status=404)

            if not user_message:
                return JsonResponse({"error": "Message cannot be empty"}, status=400)

            # await sync_to_async(user_profile.reset_token_usage_if_needed)() This was done by the middleware

            daily_token_remaining = daily_token - user_profile.ai_tokens_used_today
            
            availble_tokens = daily_token_remaining + user_profile.ai_tokens_available
            # print("Total Tokens: ", availble_tokens)
            # availble_tokens = 0

            if availble_tokens <= 0:
                return JsonResponse({"todat_limit_hit": True})

            max_token = 3000
            if max_token > availble_tokens:
                max_token = availble_tokens

            response_data = await get_ai_response(user_message, messages, max_token)  # ✅ Await once
            ai_response, prompt_tokens, completion_tokens, total_tokens = response_data  # ✅ Unpack

            # Async ORM update
            await update_user_tokens(user_profile, total_tokens, daily_token_remaining, daily_token)

            return JsonResponse({
                "response": ai_response,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)



@require_http_methods([ "POST"])
def buy_ai_tokens(request):
    if request.method == 'POST':
        data = request.POST

        token_amount = data.get('amount', '')
        payment_method = data.get('pm_id', '')

        plan_id = 'ai-tokens'

        context = {"error": '', 'title': plan_id}

        if not token_amount:
            context["error"] = 'No token amount has been specified, please try again.'
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#add-"+context['title']+"-form-errors")

        if int(token_amount) < 100000:
            context["error"] = 'Minimum token amount is 500,000.'
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#add-"+context['title']+"-form-errors")

        price_per_token = 1 / 100000  # $1 per 100,000 tokens
        price = int(token_amount) * price_per_token * 100  # Convert to cents for Stripe
   
        if not payment_method or payment_method == "None":
            context["error"] = 'No payment method has been detected.'
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#add-"+context['title']+"-form-errors")

        profile_user = request.user_profile
        customer_id = profile_user.customer_id

        try:
            stripe.PaymentMethod.attach(
                payment_method,
                customer=customer_id,
            )
        except Exception as e:
            context["error"] = 'Attached payment to customer '+str(e)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#add-"+context['title']+"-form-errors")

        try:
            metadata = {
                "profile_user_id": str(profile_user.id), 
            }

            payment_intent = stripe.PaymentIntent.create(
                amount=int(price),
                currency="usd",
                payment_method=payment_method,
                confirm=True,
                customer=customer_id,
                description=str(token_amount) + " | AI Tokens",
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                metadata=metadata,            
            )          

            user_profile = request.user_profile 

            new_available_token = user_profile.ai_tokens_available + int(token_amount)

            user_profile.ai_tokens_available = new_available_token
            user_profile.save()

            is_settings = request.GET.get('settings', '') == 'true'
            # print("GET Parameters:", request.GET.dict(), "Settings:", is_settings)

            if is_settings:
                response = render(request, 'include/settings/ai_tokens.html', context)
                return retarget(response, "#setting-ai-tokens")
            
            response = render(request, 'include/ai_tokens_form.html', context)
            return retarget(response, "#div-ai_tokens_form")
            

        except Exception as e:
            context["error"] = str(e)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#add-"+context['title']+"-form-errors")