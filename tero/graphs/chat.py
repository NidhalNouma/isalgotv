
from typing import TypedDict, Annotated, List, Tuple, Literal
import operator
import json

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from django.contrib.auth.models import User

from tero.models import ChatSession, ChatMessage
from tero.graphs.token_callback import TokenUsageCallbackHandler

from tero.graphs.shared_nodes import reflect_conversation


# Local services & tools
from tero.graphs.services import (
    build_vector_store_from_text,  
    retrieve_context_from_vector_store,
)
from tero.graphs.tools import (
    automate_broker_docs,
    alerts_docs,
    strategy_install_and_setup_docs,
)

class ChatState(TypedDict):
    user_message: str
    ai_response: str

    chat_session: ChatSession

    reflect_conversation: dict

    recent_messages: List[BaseMessage]


    topic: Literal["automate_trades", "broker_connection", "strategy_info", "none"]
    need_extra_info: bool
    context: str



def _get_llm() -> ChatOpenAI:
    """Default OpenAI chat model. Configure via env vars if desired.
    Requires OPENAI_API_KEY in environment.
    """
    # You can change the model name here if you prefer
    return ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)


def _llm_json(system: str, user: str, expect_keys: list[str]) -> dict:
    """Ask the LLM to return strict JSON and parse it defensively.
    `expect_keys` is used to ensure missing keys are added with None.
    """
    llm = _get_llm()
    messages = [
        ("system", system + " Always respond with a single JSON object and nothing else."),
        ("user", user),
    ]
    # LangChain ChatOpenAI accepts dict message format via .invoke with BaseMessages, but
    # for simplicity we pass as a list of tuples (role, content) which LangChain supports.
    resp = llm.invoke(messages)
    text = getattr(resp, "content", "")
    # Try to extract JSON from the response
    try:
        data = json.loads(text)
    except Exception:
        # Attempt to find the first/last braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except Exception:
                data = {}
        else:
            data = {}
    # Ensure expected keys exist
    for k in expect_keys:
        data.setdefault(k, None)
    return data


def router_node(state: ChatState, *_args, **_kwargs) -> ChatState:
    """First node: use an OpenAI model to classify topic & decide if extra info is needed."""
    user_message = state["user_message"]
    system = (
        "You classify a user's trading question. Choose a topic label from: "
        "['automate_trades','broker_connection','strategy_info','none'] and a boolean need_extra_info."
        " Only return JSON."
    )
    user = (
        "Message: " + user_message +
        "\nReturn JSON with keys: topic (string label) and need_extra_info (true/false)."
    )
    data = _llm_json(system, user, ["topic", "need_extra_info"])
    topic = data.get("topic") or "none"
    if topic not in {"automate_trades", "broker_connection", "strategy_info", "none"}:
        topic = "none"
    need = bool(data.get("need_extra_info"))
    return {"topic": topic, "need_extra_info": need}


def tool_context_node(state: ChatState, *_args, **_kwargs) -> ChatState:
    """Use the model to decide which tool fits best, craft a query, call it, then summarize context."""
    user_message = state["user_message"]
    topic = state.get("topic", "none")

    tool_map: dict[str, Tool | callable] = {
        "automate_trades": alerts_docs,
        "broker_connection": automate_broker_docs,
        "strategy_info": strategy_install_and_setup_docs,
    }

    tool_or_callable = tool_map.get(topic)
    if tool_or_callable is None:
        return {"context": ""}

    # llm = _get_llm().bind_tools([alerts_docs, automate_broker_docs, strategy_install_and_setup_docs])

    # Ask the LLM to craft a focused query for the tool
    system = (
        "You help craft a concise query (max 200 chars) to retrieve exact docs for the given topic."
        " Return JSON with 'query'."
    )
    user = f"Topic: {topic}\nUser message: {user_message}\nOutput keys: query"
    plan = _llm_json(system, user, ["query"])
    crafted_query = (plan.get("query") or user_message).strip()

    try:
        # Invoke the tool (LangChain Tool or plain callable)
        if isinstance(tool_or_callable, Tool):
            raw = tool_or_callable.invoke(crafted_query)
        else:
            raw = tool_or_callable(crafted_query)  # type: ignore[misc]
        raw_text = raw if isinstance(raw, str) else str(raw)
    except Exception as e:  # noqa: BLE001
        return {"context": f"[tools_error] {e}"}

    # Summarize/normalize the tool output using the LLM
    system = (
        "You summarize technical docs into a crisp context block for downstream answering."
        " Keep it factual, 5-10 bullet points or a short paragraph."
        " Return plain text, no JSON."
    )
    llm = _get_llm()
    messages = [("system", system), ("user", f"User: {user_message}\nDocs:\n{raw_text}")]
    summary = llm.invoke(messages).content or ""
    return {"context": summary.strip()}


def vector_context_node(state: ChatState, *_args, **_kwargs) -> ChatState:
    """Use the model to craft a narrow retriever query, fetch from vector store, then summarize."""
    user_message = state["user_message"]
    prior = state.get("context", "")

    # Ask LLM for a retrieval query
    system = (
        "Given a user message and any prior context, craft a concise semantic search query (<= 160 chars)"
        " to retrieve missing specifics. Return JSON with key 'query'."
    )
    user = f"User: {user_message}\nPriorContext:\n{prior}\nOutput keys: query"
    plan = _llm_json(system, user, ["query"])
    q = (plan.get("query") or user_message).strip()

    try:
        retrieved = retrieve_context_from_vector_store(q)
        retrieved_text = retrieved if isinstance(retrieved, str) else str(retrieved)
    except Exception as e:  # noqa: BLE001
        return {"context": f"[retriever_error] {e}"}

    # Summarize/merge with prior using LLM
    llm = _get_llm()
    system = (
        "Merge the new retrieved snippets with any prior context into a single, deduplicated context block."
        " Prefer specifics (endpoints, parameters, steps). Return plain text."
    )
    messages = [
        ("system", system),
        ("user", f"Prior:\n{prior}\n\nRetrieved:\n{retrieved_text}"),
    ]
    merged = llm.invoke(messages).content or ""
    return {"context": merged.strip()}

def responder_node(state: ChatState, *_args, **_kwargs) -> ChatState:
    """Use the model to produce the final answer from the current context and the user message."""
    user_message = state["user_message"]
    topic = state.get("topic", "none")
    context = state.get("context", "").strip()

    llm = _get_llm()
    system = (
        "You are a precise trading assistant. Use the provided context to answer."
        " If context is thin, ask up to 2 targeted follow-up questions at the end."
        " Output should be clear steps or a short explanation; include code or cURL only if essential."
    )
    messages = [
        ("system", system),
        ("user", f"Topic: {topic}\nUser: {user_message}\nContext:\n{context}"),
    ]
    answer = llm.invoke(messages).content or ""

    state["ai_response"] = answer.strip()
    return state

def summarize(state: ChatState):
    current_messages = state["messages"]
    reflect_conversation_obj = state.get("reflect_conversation", {})

    reflect_conversation_obj = reflect_conversation(reflect_conversation_obj, messages=current_messages)
    state["reflect_conversation"] = reflect_conversation_obj

    return state

def chatbot_node(state: ChatState):
    llm = ChatOpenAI(model="gpt-4o")
    ai_msg = llm.invoke(state["messages"])  # returns an AIMessage
    # Return in state-update shape so the graph can merge messages correctly
    return {"messages": [ai_msg]}

def create_langgraph_agent():
    graph = StateGraph(ChatState)

    graph.add_node("summarize", summarize)
    graph.add_node("chatbot", chatbot_node)

    graph.set_entry_point("summarize")

    graph.add_edge("summarize", "chatbot")
    graph.add_edge("chatbot", END)

    return graph.compile()

# Create the LangGraph agent
langgraph_agent = create_langgraph_agent()


def process_chat_message(chat_session: ChatSession, chat_messages, user_message_content: str) -> Tuple[str, dict]:
    """Processes a chat message using LangGraph and returns the AI's response and token usage."""

    input_messages = [HumanMessage(content=user_message_content)]

    token_callback = TokenUsageCallbackHandler()

    response = langgraph_agent.invoke(
        {"user_message": input_messages, "recent_messages": chat_messages, "chat_session": chat_session},
        config={
            "callbacks": [token_callback],
        },
    )
    
    ai_response_message = response["messages"][-1]
    ai_response_content = ai_response_message.content


    token_usage = token_callback.get_token_usage()

    return ai_response_content, token_usage

