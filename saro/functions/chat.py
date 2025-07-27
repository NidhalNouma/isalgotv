import textwrap

from asgiref.sync import sync_to_async

from saro.models import ChatSession, ChatMessage

from .chat_service import ChatService
from .docs import get_system_content



@sync_to_async
def get_ai_response(user_message, messages, max_token) -> tuple:
    print(f"User message: {user_message}")

    chat_service = ChatService()
    chat_service.build_vector_store_from_text(get_system_content())

    chat_history = []

    for msg in messages:
        chat_history.append({"role": msg['role'], "content": msg["content"]})

    try:

        response = chat_service.generate_response(
            user_question=user_message,
            message_history=chat_history
        )

        ai_response = response.get('response', '')
        prompt_tokens = response.get('prompt_tokens', 0)
        completion_tokens = response.get('completion_tokens', 0)
        total_tokens = response.get('total_tokens', 0)

        return ai_response, prompt_tokens, completion_tokens, total_tokens
    except Exception as e:
        print(f"AI error: {str(e)}")
        raise Exception(f"{str(e)}")

@sync_to_async
def create_chat_session(user, user_message=""):
    if user_message:
        # Generate a concise, meaningful summary up to 30 characters
        title = textwrap.shorten(
            user_message.strip().replace("\n", " "),
            width=30,
            placeholder="..."
        )
    else:
        title = "New Chat"
    session = ChatSession.objects.create(user=user, title=title)

    session_json = {
        "id": session.id,
        "user": session.user.username,
        "title": session.title,
        "created_at": session.created_at,
        "last_updated": session.last_updated,
        "summary": session.summary
    }

    return session_json, session

@sync_to_async
def add_chat_message(session, role, content, reply_to=None, liked=None, embedding=None, token_used=0):
    message = ChatMessage.objects.create(
        session=session,
        role=role,
        content=content,
        liked=liked,
        reply_to=reply_to,
        embedding=embedding,
        token_used=token_used
    )
    session.last_updated = message.created_at
    session.read = False  # Mark session as unread when a new message is added
    session.save()

    message_json = {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "liked": message.liked,
        "created_at": message.created_at
    }
    return message_json, message

def get_sessions_for_user(user):
    sessions = ChatSession.objects.filter(user=user).order_by('-last_updated')
    return [
        {
            "id": session.id,
            "title": session.title,
            "read": session.read,
            "created_at": session.created_at,
            "last_updated": session.last_updated,
            "summary": session.summary
        }
        for session in sessions
    ]

def get_limit_chat_sessions(user, start=0, limit=10):
    sessions = ChatSession.objects.filter(user=user).order_by('-last_updated')[start:start+limit]
    chats = [
        {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at,
            "read": session.read,
            "last_updated": session.last_updated,
            "summary": session.summary,
        }
        for session in sessions
    ]

    return {
        "sessions": chats,
        "is_last_page": True if len(sessions) < limit else False,
    }

def get_chat_messages(session):
    messages = session.messages.all().order_by('created_at')
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "liked": msg.liked,
            "created_at": msg.created_at
        }
        for msg in messages
    ]

def get_limit_chat_messages(session_id, start=0, limit=10):
    session = ChatSession.objects.get(id=session_id)
    # Fetch messages in descending order (newest first), paginated
    messages = session.messages.all().order_by('-created_at')[start:start+limit]
    # print("get_limit_chat_messages -> " ,len(messages), limit)
    messages = messages[::-1]  # Reverse to maintain chronological order
    messages = [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "liked": msg.liked,
            "created_at": msg.created_at,
        }
        for msg in messages
    ]

    return {
        "messages": messages,
        "session": {
            "id": session.id,
            "user": session.user.username,
            "title": session.title,
            "created_at": session.created_at,
            "last_updated": session.last_updated,
            "summary": session.summary
        },
        "is_last_page": True if len(messages) < limit else False
    }


@sync_to_async
def get_chat_session(session_id):
    try:
        session = ChatSession.objects.get(id=session_id)
        session_json = {
            "id": session.id,
            "user": session.user.username,
            "title": session.title,
            "created_at": session.created_at,
            "last_updated": session.last_updated,
            "summary": session.summary
        }
        return session_json, session
    except ChatSession.DoesNotExist:
        return None
    
def update_chat_session(session_id, title=None, summary=None, read=None):
    try:
        session = ChatSession.objects.get(id=session_id)

        update_fields = []
        if title is not None:
            session.title = title
            update_fields.append('title')
        if summary is not None:
            session.summary = summary
            update_fields.append('summary')
        if read is not None:
            if session.read == read:
                print(f"Session {session_id} already has read={read}, skipping update.")
            else:
                session.read = read
                update_fields.append('read')

        if update_fields:
            session.save(update_fields=update_fields)
            
        # Reload to get fresh data
        session.refresh_from_db()

        session_json = {
            "id": session.id,
            "title": session.title,
            "summary": session.summary,

            "user": session.user.username,
            "created_at": session.created_at,
            "last_updated": session.last_updated,
        }
        return session_json, session
    except ChatSession.DoesNotExist:
        return None
    
def delete_chat_session(session_id):
    try:
        session = ChatSession.objects.get(id=session_id)
        session.delete()
        return True
    except ChatSession.DoesNotExist:
        return False
    
def like_chat_message(message_id):
    try:
        message = ChatMessage.objects.get(id=message_id)
        message.liked = True
        message.save()
        return {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "liked": message.liked,
            "created_at": message.created_at
        }
    except ChatMessage.DoesNotExist:
        return None
    
def dislike_chat_message(message_id):
    try:
        message = ChatMessage.objects.get(id=message_id)
        message.liked = False
        message.save()
        return {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "liked": message.liked,
            "created_at": message.created_at
        }
    except ChatMessage.DoesNotExist:
        return None