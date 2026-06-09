
from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _

from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRedirect, retarget

from .functions.chat import *
from .models import ChatMessage

from proxy.views import proxy_view

from asgiref.sync import sync_to_async, async_to_sync
import environ

import json
import stripe

env = environ.Env()
stripe.api_key = env('STRIPE_API_KEY')

def index(request):
    context = {
        "ai_models": [
            { "name": "TR-01", "description": "Best for common use" },
            # { "name": "TR-H6 ", "description": "Best for reasoning" }
        ]
    }
    return render(request, "tero/index.html", context=context)

def chat_index(request, id):
    context = {
        "ai_models": [
            { "name": "TR-01", "description": "Best for common use" },
            # { "name": "TR-H6 ", "description": "Best for reasoning" }
        ]
    }
    return render(request, "tero/index.html", context=context)

def tero_404(request, exception):
    return render(request, "tero/404.html", status=404)
def tero_404_preview(request):
    return render(request, "tero/404.html", status=404)

def get_chat_sessions(request, start=0):
    if request.method == "POST":
        try:
            if request.user.is_authenticated:
                limit = 25
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
            return JsonResponse({"error": _("Failed to retrieve chat sessions")}, status=500)
        
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
            else:
                raise Exception("User/Chat doesn't exist")
        except Exception as e:
            print(f"Error in get_chat_messages: {e}")
            return JsonResponse({"error": _("Failed to retrieve chat messages")}, status=500)
        
def create_chat(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            data = json.loads(request.body)
            title = data.get("title", "").strip()
            message = data.get("message", "")
            answer = data.get("answer", "")

            if not title:
                return JsonResponse({"error": _("Title cannot be empty")}, status=400)
            
            if not message:
                return JsonResponse({"error": _("Message cannot be empty")}, status=400)
            
            if not answer:
                return JsonResponse({"error": _("Answer cannot be empty")}, status=400)
            

            session_json, session = create_chat_session(request.user, title)

            if not session:
                return JsonResponse({"error": _("Failed to create chat session")}, status=500)
            
            user_message_json, user_message = add_chat_message(session, "user", message)
            system_answer_json, system_answer = add_chat_message(session, "assistant", answer, reply_to=user_message)

            context = {
                "chat_session": session_json,
                "user_message": user_message_json,
                "system_answer": system_answer_json,
            }
            return JsonResponse(context)
        
        else:
            raise Exception("User/Chat doesn't exist")
    
def update_chat(request, session_id):
    if request.method == "POST":
        if request.user.is_authenticated:
            data = json.loads(request.body)
            title = data.get("title", "").strip()

            if not session_id:
                return JsonResponse({"error": _("Session ID is required")}, status=400)
            
            if not title:
                return JsonResponse({"error": _("Title cannot be empty")}, status=400)

            session_json, session = update_chat_session(session_id, title=title)

            return JsonResponse({"success": True, "message": _("Chat session updated successfully"), "chat_session": session_json})
                
def chat_read(request, session_id):
    if request.method == "POST":
        if request.user.is_authenticated:
            data = json.loads(request.body)

            if not session_id:
                return JsonResponse({"error": _("Session ID is required")}, status=400)
            
            session_json, session = update_chat_session(session_id, read=True)

            return JsonResponse({"success": True, "message": _("Chat session updated successfully"), "chat_session": session_json})


def like_message(request, message_id):
    if request.method == "POST":
        try:
            if not request.user.is_authenticated:
                raise Exception("User/Chat doesn't exist")

            message = like_chat_message(message_id)
            if not message:
                return JsonResponse({"error": _("Message not found")}, status=404)

            return JsonResponse({"message": message})
        except Exception as e:
            print(f"Error in like_message: {e}")
            return JsonResponse({"error": _("Failed to like chat message")}, status=500)


def dislike_message(request, message_id):
    if request.method == "POST":
        try:
            if not request.user.is_authenticated:
                raise Exception("User/Chat doesn't exist")

            message = dislike_chat_message(message_id)
            if not message:
                return JsonResponse({"error": _("Message not found")}, status=404)

            return JsonResponse({"message": message})
        except Exception as e:
            print(f"Error in dislike_message: {e}")
            return JsonResponse({"error": _("Failed to dislike chat message")}, status=500)
        
def delete_chat(request, session_id):
    if request.method == "POST":
        if request.user.is_authenticated:
            delete_chat_session(session_id)

            return JsonResponse({"success": True, "message": _("Chat session deleted successfully")})
        
def new_chat_message(request, session_id):
    if request.method == "POST":
        if request.user.is_authenticated:
            data = json.loads(request.body)
            message = data.get("message", "").strip()
            answer = data.get("answer", "").strip()

            if not session_id:
                return JsonResponse({"error": _("Session ID is required")}, status=400)
            
            if not message:
                return JsonResponse({"error": _("Message cannot be empty")}, status=400)

            chat_session_json, chat_session = get_chat_session(session_id)
            if not chat_session:
                return JsonResponse({"error": _("Chat session not found")}, status=404)

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

            system_content = "get_system_content()"
            context = {
                "system_content": system_content,
            }

            response = render(request, 'include/settings/ai_system_content.html', context)
            return response

@sync_to_async
def update_user_tokens(user_profile, total_tokens):
    """ Update user AI token usage safely in async context. """
    tokens = user_profile.ai_free_daily_tokens_available - total_tokens 
     
    print("Total Tokens: ", total_tokens, "Daily Token Remaining: ", tokens) 

    if tokens < 0:
        new_available_tokens = user_profile.ai_tokens_available - abs(tokens)
        if new_available_tokens < 0:
            new_available_tokens = 0
        user_profile.ai_tokens_available = new_available_tokens
        user_profile.ai_free_daily_tokens_available = 0
    else:
        user_profile.ai_free_daily_tokens_available -= total_tokens

    user_profile.save()  
    
    return user_profile


async def ai_chat_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("userMessage", "").strip()
            messages = data.get("messages", [])
            chat_id = data.get("chatId", None)
            model = data.get("model", "GPT-4o") 

            user_profile = request.user_profile
            if not user_profile:
                return JsonResponse({"error": _("User not found")}, status=404)

            if not user_message:
                return JsonResponse({"error": _("Message cannot be empty")}, status=400)

            # await sync_to_async(user_profile.reset_token_usage_if_needed)() This was done by the middleware

            
            availble_tokens = user_profile.ai_free_daily_tokens_available + user_profile.ai_tokens_available
            # availble_tokens = 0

            if availble_tokens <= 0:
                return JsonResponse({"todat_limit_hit": True})

            max_token = 3000
            if max_token > availble_tokens:
                max_token = availble_tokens

            response_data = await get_ai_response(user_message, messages, max_token)  # ✅ Await once
            ai_response, prompt_tokens, completion_tokens, total_tokens = response_data  # ✅ Unpack
            # Async ORM update
            user_profile = await update_user_tokens(user_profile, total_tokens)

            if chat_id and str.find(str(chat_id), 'new') == -1:
                chat_session_json, chat_session = await get_chat_session(chat_id)
                if chat_session:
                    user_message_json, user_message_obj = await add_chat_message(chat_session, "user", user_message)
                    system_answer_json, system_answer = await add_chat_message(chat_session, "assistant", ai_response, reply_to=user_message_obj, token_used=total_tokens)

                    chat_session_json["read"] = False  # Mark as unread

            else:
                chat_session_json, chat_session = await create_chat_session(request.user, user_message)

                if not chat_session:
                    return JsonResponse({"error": _("Failed to create chat session")}, status=500)
                
                user_message_json, user_message = await add_chat_message(chat_session, "user", user_message)
                system_answer_json, system_answer = await add_chat_message(chat_session, "assistant", ai_response, reply_to=user_message, token_used=total_tokens)


            return JsonResponse({
                "answer": ai_response,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,

                "ai_tokens_available": user_profile.ai_tokens_available,
                "ai_free_daily_tokens_available": user_profile.ai_free_daily_tokens_available,

                "chat_session": chat_session_json,
                "user_message": user_message_json,
                "system_answer": system_answer_json,    
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": _("Invalid JSON format")}, status=400)
        except Exception as e:
            print(f"Ai response Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": _("Invalid request method")}, status=405)


def stream_ai_reply(request):
    data = json.loads(request.body)

    user_message_ = data.get("userMessage", "").strip()
    messages = data.get("messages", [])
    chat_id = data.get("chatId", None)
    parent_message_id = data.get("parentMessageId", None)
    model = data.get("model", "TR-01")
    msg_context = data.get("context", None)

    def event_stream():
        full_response = ""
        cancelled = False
        try:
            user_profile = request.user_profile

            if not user_profile:
                raise Exception(_("User not found"))

            if not user_message_:
                raise Exception(_("Message cannot be empty!"))
                    
            availble_tokens = user_profile.ai_free_daily_tokens_available + user_profile.ai_tokens_available

            if availble_tokens <= 0:
                 yield "\n<|limit|>:" + f'limit tokens reached ({availble_tokens})'
                 return
            
            token_tracker = {}
            token_stream = get_ai_stream_response(user_message_, messages, max_token=4000, token_tracker=token_tracker, msg_context=msg_context)
            for chunk in token_stream:
                try:
                    # Check if chunk is an agent state marker
                    if chunk.startswith("<|AGENT_STATE:") and chunk.endswith("|>"):
                        # Extract state name (e.g., "thinking" from "<|AGENT_STATE:thinking|>")
                        state_name = chunk[14:-2]  # Skip "<|AGENT_STATE:" and end "|>"
                        yield "\n<|state|>:" + state_name
                    else:
                        # Regular content chunk
                        full_response += chunk
                        yield "\n<|data|>:" + chunk
                except (GeneratorExit, ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                    # Client cancelled/closed connection mid-stream
                    cancelled = True
                    break

            if cancelled:
                # Do not persist or charge tokens on cancel; just stop streaming quietly
                return

            # Use real token counts from the stream
            total_tokens = token_tracker.get("total_tokens", 0)
            user_profile = async_to_sync(update_user_tokens)(user_profile, total_tokens)

            if chat_id and str.find(str(chat_id), 'new') == -1:
                chat_session_json, chat_session = async_to_sync(get_chat_session)(chat_id)
                if chat_session:
                    parent_msg = None
                    if parent_message_id is not None:
                        try:
                            parent_msg = chat_session.messages.get(id=parent_message_id)
                        except ChatMessage.DoesNotExist:
                            parent_msg = None
                    if parent_msg is None:
                        parent_msg = chat_session.messages.order_by('-created_at').first()

                    user_message_json, user_message_obj = async_to_sync(add_chat_message)(chat_session, "user", user_message_, msg_context=msg_context, parent=parent_msg)
                    system_answer_json, system_answer = async_to_sync(add_chat_message)(chat_session, "assistant", full_response, reply_to=user_message_obj, token_used=total_tokens, msg_context=msg_context, parent=user_message_obj)

                    chat_session_json["read"] = False  # Mark as unread

            else:
                chat_session_json, chat_session = async_to_sync(create_chat_session)(request.user, user_message_)

                if not chat_session:
                    raise Exception(_("Failed to create chat session"))
                
                user_message_json, user_message =  async_to_sync(add_chat_message)(chat_session, "user", user_message_, msg_context=msg_context)
                system_answer_json, system_answer = async_to_sync(add_chat_message)(chat_session, "assistant", full_response, reply_to=user_message, token_used=total_tokens, msg_context=msg_context, parent=user_message)

            # Ensure the final message starts on a new line and is newline-delimited
            yield "\n<|done|>:" + json.dumps({
                    "done": True,
                    "answer": full_response,
                    "prompt_tokens": total_tokens,
                    "completion_tokens": total_tokens,
                    "total_tokens": total_tokens,

                    "ai_tokens_available": user_profile.ai_tokens_available,
                    "ai_free_daily_tokens_available": user_profile.ai_free_daily_tokens_available,

                    "chat_session": chat_session_json,
                    "user_message": user_message_json,
                    "system_answer": system_answer_json,
                }, default=str) 
        except Exception as e:
            yield "\n<|error|>:" + str(e)
            return

        # add_chat_message(chat_id, role="user", content=user_message)
        # add_chat_message(chat_id, role="assistant", content=full_response)
    
    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    # Headers that reduce buffering/caching
    resp["Cache-Control"] = "no-cache, no-transform"
    resp["X-Accel-Buffering"] = "no"     # helps when an nginx is in the chain
    resp["Content-Encoding"] = "identity" # avoid gzip buffering
    return resp


def branch_message(request, message_id):
    """Edit a user message and create a new conversation branch with AI response."""
    data = json.loads(request.body)
    new_content = data.get("message", "").strip()
    msg_context = data.get("context", None)

    def event_stream():
        full_response = ""
        cancelled = False
        try:
            user_profile = request.user_profile
            if not user_profile:
                raise Exception(_("User not found"))
            if not new_content:
                raise Exception(_("Message cannot be empty!"))

            original_msg = ChatMessage.objects.get(id=message_id)
            session = original_msg.session

            # Back-fill parent chain for legacy messages
            ensure_parent_chain(session)
            original_msg.refresh_from_db()

            parent = original_msg.parent  # Same parent → makes new msg a sibling

            # Build history up to (and including) the parent
            history_msgs = get_history_up_to(parent) if parent else []
            messages = [{"role": m.role, "content": m.content} for m in history_msgs]

            available_tokens = user_profile.ai_free_daily_tokens_available + user_profile.ai_tokens_available
            if available_tokens <= 0:
                yield "\n<|limit|>:limit tokens reached"
                return

            token_tracker = {}
            token_stream = get_ai_stream_response(
                new_content, messages, max_token=4000,
                token_tracker=token_tracker, msg_context=msg_context,
            )

            for chunk in token_stream:
                try:
                    # Check if chunk is an agent state marker
                    if chunk.startswith("<|AGENT_STATE:") and chunk.endswith("|>"):
                        # Extract state name (e.g., "thinking" from "<|AGENT_STATE:thinking|>")
                        state_name = chunk[14:-2]  # Skip "<|AGENT_STATE:" and end "|>"
                        yield "\n<|state|>:" + state_name
                    else:
                        # Regular content chunk
                        full_response += chunk
                        yield "\n<|data|>:" + chunk
                except (GeneratorExit, ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                    cancelled = True
                    break

            if cancelled:
                return

            total_tokens = token_tracker.get("total_tokens", 0)
            user_profile = async_to_sync(update_user_tokens)(user_profile, total_tokens)

            # Persist new branch messages
            user_msg_json, user_msg = async_to_sync(add_chat_message)(
                session, "user", new_content,
                msg_context=msg_context, parent=parent,
            )
            ai_msg_json, ai_msg = async_to_sync(add_chat_message)(
                session, "assistant", full_response,
                reply_to=user_msg, token_used=total_tokens,
                msg_context=msg_context, parent=user_msg,
            )

            session_json = {
                "id": session.id,
                "user": session.user.username,
                "title": session.title,
                "created_at": str(session.created_at),
                "last_updated": str(session.last_updated),
            }

            yield "\n<|done|>:" + json.dumps({
                "done": True,
                "answer": full_response,
                "total_tokens": total_tokens,
                "ai_tokens_available": user_profile.ai_tokens_available,
                "ai_free_daily_tokens_available": user_profile.ai_free_daily_tokens_available,
                "chat_session": session_json,
                "user_message": user_msg_json,
                "system_answer": ai_msg_json,
                "branch_from": message_id,
            }, default=str)
        except Exception as e:
            yield "\n<|error|>:" + str(e)

    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache, no-transform"
    resp["X-Accel-Buffering"] = "no"
    resp["Content-Encoding"] = "identity"
    return resp


def switch_branch(request, message_id):
    """Return the message and its descendants (following latest children)."""
    if request.method == "POST":
        try:
            msgs = get_branch_messages(message_id)
            return JsonResponse({"messages": serialize_branch_messages(msgs)})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@require_http_methods([ "POST"])
def buy_ai_tokens(request):
    if request.method == 'POST':
        data = request.POST

        token_amount = data.get('amount', '')
        payment_method = data.get('pm_id', '')

        plan_id = 'ai-tokens'

        context = {"error": '', 'title': plan_id}

        if not token_amount:
            context["error"] = _('No token amount has been specified, please try again.')
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#add-"+context['title']+"-form-errors")

        if int(token_amount) < 100000:
            context["error"] = _('Minimum token amount is 500,000.')
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#add-"+context['title']+"-form-errors")

        price_per_token = 1 / 100000  # $1 per 100,000 tokens
        price = int(token_amount) * price_per_token * 100  # Convert to cents for Stripe
   
        if not payment_method or payment_method == "None":
            context["error"] = _('No payment method has been detected.')
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#add-"+context['title']+"-form-errors")

        profile_user = request.user_profile
        customer_id = profile_user.customer_id_value

        try:
            stripe.PaymentMethod.attach(
                payment_method,
                customer=customer_id,
            )
        except Exception as e:
            context["error"] = _('Attached payment to customer ') + str(e)
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

            user_profile = user_profile.get_with_update_stripe_data(force=True)
            context['user_profile'] = user_profile
            
            is_settings = request.GET.get('settings', '') == 'true'

            if is_settings:
                response = render(request, 'include/settings/ai_tokens.html', context)
                return retarget(response, "#setting-ai-tokens")
            
            response = render(request, 'include/ai_tokens_form.html', context)
            return retarget(response, "#add-ai-tokens-form")
            

        except Exception as e:
            context["error"] = str(e)
            response = render(request, 'include/errors.html', context)
            return retarget(response, "#add-"+context['title']+"-form-errors")