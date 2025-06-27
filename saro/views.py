
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse

from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRedirect, retarget

from .functions.chat import *

from asgiref.sync import sync_to_async
import environ

import json
import stripe

env = environ.Env()
stripe.api_key = env('STRIPE_API_KEY')

# Create your views here.
def index(request):
    return render(request, "saro/index.html")

def get_chat_sessions(request, start=0):
    if request.method == "POST":
        try:
            if request.user.is_authenticated:
                limit = 50
                response = get_limit_chat_sessions(request.user, start, limit)

                context = {
                    "chat_sessions": response.get("sessions", []),
                    "is_last_page": response.get("is_last_page", False),
                    "start": start,
                    "limit": limit,
                }

                return JsonResponse(context)
        except Exception as e:
            print(f"Error in get_chat_sessions: {e}")
            return JsonResponse({"error": "Failed to retrieve chat sessions"}, status=500)
        
def get_chat_messages(request, session_id, start=0):
    if request.method == "POST":
        try:
            if request.user.is_authenticated:
                limit = 40
                chat_messages = get_limit_chat_messages(session_id, start, limit)

                context = {
                    "chat_messages": chat_messages.get("messages", []),
                    "session": chat_messages.get("session", {}),
                    "is_last_page": chat_messages.get("is_last_page", False),
                    "limit": limit,
                    "start": start,
                }

                return JsonResponse(context)
        except Exception as e:
            print(f"Error in get_chat_messages: {e}")
            return JsonResponse({"error": "Failed to retrieve chat messages"}, status=500)
        
def create_chat(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            data = json.loads(request.body)
            title = data.get("title", "").strip()
            message = data.get("message", "")
            answer = data.get("answer", "")

            if not title:
                return JsonResponse({"error": "Title cannot be empty"}, status=400)
            
            if not message:
                return JsonResponse({"error": "Message cannot be empty"}, status=400)
            
            if not answer:
                return JsonResponse({"error": "Answer cannot be empty"}, status=400)
            

            session_json, session = create_chat_session(request.user, title)

            if not session:
                return JsonResponse({"error": "Failed to create chat session"}, status=500)
            
            user_message_json, user_message = add_chat_message(session, "user", message)
            system_answer_json, system_answer = add_chat_message(session, "assistant", answer, reply_to=user_message)

            context = {
                "chat_session": session_json,
                "user_message": user_message_json,
                "system_answer": system_answer_json,
            }
            return JsonResponse(context)
        
def update_chat(request, session_id):
    if request.method == "POST":
        if request.user.is_authenticated:
            data = json.loads(request.body)
            title = data.get("title", "").strip()

            if not session_id:
                return JsonResponse({"error": "Session ID is required"}, status=400)
            
            if not title:
                return JsonResponse({"error": "Title cannot be empty"}, status=400)

            session_json, session = update_chat_session(session_id, title)

            return JsonResponse({"success": True, "message": "Chat session updated successfully", "chat_session": session_json})
        
def delete_chat(request, session_id):
    if request.method == "POST":
        if request.user.is_authenticated:
            delete_chat_session(session_id)

            return JsonResponse({"success": True, "message": "Chat session deleted successfully"})
        
def new_chat_message(request, session_id):
    if request.method == "POST":
        if request.user.is_authenticated:
            data = json.loads(request.body)
            message = data.get("message", "").strip()
            answer = data.get("answer", "").strip()

            if not session_id:
                return JsonResponse({"error": "Session ID is required"}, status=400)
            
            if not message:
                return JsonResponse({"error": "Message cannot be empty"}, status=400)

            chat_session_json, chat_session = get_chat_session(session_id)
            if not chat_session:
                return JsonResponse({"error": "Chat session not found"}, status=404)

            user_message_json, user_message = add_chat_message(chat_session, "user", message)
            system_answer_json, system_answer = add_chat_message(chat_session, "assistant", answer, reply_to=user_message)

            context = {
                "chat_session": chat_session_json,
                "user_message": user_message_json,
                "system_answer": system_answer_json,
            }
            return JsonResponse(context)

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
            chat_id = data.get("chatId", None)

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

            # import asyncio
            # await asyncio.sleep(3)

            # print('user ', user_message)

            if availble_tokens <= 0:
                return JsonResponse({"todat_limit_hit": True})

            max_token = 3000
            if max_token > availble_tokens:
                max_token = availble_tokens

            response_data = await get_ai_response(user_message, messages, max_token)  # ✅ Await once
            ai_response, prompt_tokens, completion_tokens, total_tokens = response_data  # ✅ Unpack

            # Async ORM update
            await update_user_tokens(user_profile, total_tokens, daily_token_remaining, daily_token)

            if chat_id and str.find(str(chat_id), '-new') == -1:
                chat_session_json, chat_session = await get_chat_session(chat_id)
                if chat_session:
                    user_message_json, user_message_obj = await add_chat_message(chat_session, "user", user_message)
                    system_answer_json, system_answer = await add_chat_message(chat_session, "assistant", ai_response, reply_to=user_message_obj)

            else:
                chat_session_json, chat_session = await create_chat_session(request.user, user_message)

                if not chat_session:
                    return JsonResponse({"error": "Failed to create chat session"}, status=500)
                
                user_message_json, user_message = await add_chat_message(chat_session, "user", user_message)
                system_answer_json, system_answer = await add_chat_message(chat_session, "assistant", ai_response, reply_to=user_message)


            return JsonResponse({
                "answer": ai_response,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,

                "chat_session": chat_session_json,
                "user_message": user_message_json,
                "system_answer": system_answer_json,    
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


async def stream_ai_reply(request):
    user = request.user
    session_id = request.GET.get("session_id")
    user_message = request.GET.get("message", "")

    # You’d need to fetch the full chat history first
    _, session = get_chat_session(session_id)
    messages = get_chat_messages(session)

    async def event_stream():
        try:
            # Regenerate vectorstore + system prompt if needed is done internally
            response = await get_ai_response(user_message, messages, max_tokens=3000, stream=True)
            full_response = ""

            async for chunk in response:
                if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                    content = chunk["choices"][0]["delta"]["content"]
                    full_response += content
                    yield f"data: {content}\n\n"
                elif chunk.get("error"):
                    yield f"data: [Error] {chunk['error']['message']}\n\n"

            # (Optional) save the AI reply in the DB
            add_chat_message(session, role="user", content=user_message)
            add_chat_message(session, role="assistant", content=full_response)

        except Exception as e:
            yield f"data: [Error] {str(e)}\n\n"

    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')


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