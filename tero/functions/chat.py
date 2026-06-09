import textwrap

from asgiref.sync import sync_to_async

from tero.models import ChatSession, ChatMessage

from .chat_service import ChatService

def get_ai_stream_response(user_message, messages, max_token, token_tracker=None, msg_context=None):
    """Returns a synchronous generator that yields AI response tokens."""
    chat_service = ChatService()

    chat_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in messages
    ]

    try:
        token_stream = chat_service.stream_response(
            user_question=user_message,
            message_history=chat_history,
            token_tracker=token_tracker,
            msg_context=msg_context,
        )
        return token_stream
    except Exception as e:
        print(f"AI error: {str(e)}")
        raise


@sync_to_async
def get_ai_response(user_message, messages, max_token) -> tuple:
    chat_service = ChatService()

    chat_history = []

    for msg in messages:
        chat_history.append({"role": msg['role'], "content": msg["content"]})

    try:
        token_tracker = {}
        response = chat_service.stream_response(
            user_question=user_message,
            message_history=chat_history,
            token_tracker=token_tracker,
        )

        ai_response = "".join(response)
        prompt_tokens = token_tracker.get('prompt_tokens', 0)
        completion_tokens = token_tracker.get('completion_tokens', 0)
        total_tokens = token_tracker.get('total_tokens', 0)

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
    }

    return session_json, session

@sync_to_async
def add_chat_message(session, role, content, reply_to=None, liked=None, embedding=None, token_used=0, msg_context=None, parent=None):
    message = ChatMessage.objects.create(
        session=session,
        role=role,
        content=content,
        liked=liked,
        reply_to=reply_to,
        # embedding=embedding,
        token_used=token_used,
        context=msg_context,
        parent=parent,
    )
    session.last_updated = message.created_at
    session.read = False  # Mark session as unread when a new message is added
    session.save()

    message_json = {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "liked": message.liked,
        "context": message.context,
        "parent_id": message.parent_id,
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
            "context": msg.context,
            "parent_id": msg.parent_id,
            "created_at": msg.created_at
        }
        for msg in messages
    ]

def get_limit_chat_messages(session_id, start=0, limit=10):
    try:
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
                "context": msg.context,
                "parent_id": msg.parent_id,
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
            },
            "is_last_page": True if len(messages) < limit else False
        }
    except Exception as e:
        raise Exception(e)


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


# ─── Branching helpers ───────────────────────────────────────────────

def ensure_parent_chain(session):
    """Back-fill parent pointers for messages that don't have them yet."""
    messages = list(session.messages.order_by('created_at'))
    updates = []
    for i in range(1, len(messages)):
        if messages[i].parent_id is None:
            messages[i].parent = messages[i - 1]
            updates.append(messages[i])
    if updates:
        ChatMessage.objects.bulk_update(updates, ['parent'])
    return messages


def get_history_up_to(message):
    """Walk up parent chain to build the conversation history (inclusive)."""
    chain = []
    current = message
    while current:
        chain.append(current)
        current = current.parent
    chain.reverse()
    return chain


def get_branch_messages(message_id):
    """Return *message_id* and its descendants following the latest child."""
    try:
        msg = ChatMessage.objects.get(id=message_id)
    except ChatMessage.DoesNotExist:
        return []
    result = [msg]
    current = msg
    while True:
        child = current.children.order_by('-created_at').first()
        if not child:
            break
        result.append(child)
        current = child
    return result


def serialize_branch_messages(messages):
    """Serialize a list of ChatMessage model instances for JSON."""
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "liked": m.liked,
            "context": m.context,
            "parent_id": m.parent_id,
            "created_at": str(m.created_at),
        }
        for m in messages
    ]