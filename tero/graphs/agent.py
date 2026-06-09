
from typing import TypedDict, Annotated, List, Tuple
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableLambda
from django.contrib.auth.models import User

from tero.models import ChatSession, ChatMessage
from tero.graphs.token_callback import TokenUsageCallbackHandler

class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    summary: str

def summarize_conversation(state: ChatState):
    current_messages = state["messages"]
    summary = state.get("summary", "")

    if len(current_messages) > 10 or (summary and len(summary.split()) < 50):
        messages_to_summarize = current_messages[:-5] if len(current_messages) > 5 else current_messages

        summary_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that summarizes conversations. Summarize the following conversation concisely, focusing on key topics and decisions. If a previous summary exists, update it with the new information."),
            MessagesPlaceholder(variable_name="messages")
        ])

        # Shape the output to a dict with 'output' key to satisfy tracers/callbacks.
        chain = prompt | summary_llm | RunnableLambda(lambda m: {"output": m.content})
        new_summary_dict = chain.invoke({"messages": messages_to_summarize})
        new_summary_content = new_summary_dict["output"]

        return {"summary": new_summary_content, "messages": current_messages[-5:]}
    return state

def chatbot_node(state: ChatState):
    llm = ChatOpenAI(model="gpt-4o")
    ai_msg = llm.invoke(state["messages"])  # returns an AIMessage
    # Return in state-update shape so the graph can merge messages correctly
    return {"messages": [ai_msg]}

def create_langgraph_agent():
    graph = StateGraph(ChatState)

    graph.add_node("summarize", summarize_conversation)
    graph.add_node("chatbot", chatbot_node)

    graph.set_entry_point("summarize")

    graph.add_edge("summarize", "chatbot")
    graph.add_edge("chatbot", END)

    return graph.compile()

# Create the LangGraph agent
langgraph_agent = create_langgraph_agent()

# Wrap the LangGraph agent with RunnableWithMessageHistory
agent_with_history = RunnableWithMessageHistory(
    langgraph_agent,
    input_messages_key="messages",
    history_messages_key="messages",
    output_messages_key="messages",
)

def process_chat_message(user_id: int, session_id: int, user_message_content: str) -> Tuple[str, dict]:
    """Processes a chat message using LangGraph and returns the AI's response and token usage."""
    user_obj = User.objects.get(id=user_id)

    chat_session, created = ChatSession.objects.get_or_create(
        id=session_id, user=user_obj,
        defaults={
            'title': f'Chat Session {session_id}',
            'user': user_obj
        }
    )

    ChatMessage.objects.create(
        session=chat_session, role='user', content=user_message_content
    )

    input_messages = [HumanMessage(content=user_message_content)]

    token_callback = TokenUsageCallbackHandler()

    response = agent_with_history.invoke(
        {"messages": input_messages},
        config={
            "configurable": {
                # Use thread_id for LangGraph checkpointers
                "thread_id": str(session_id),
                "session_id": str(session_id),
                "user_id": str(user_id),
            },
            "callbacks": [token_callback],
        },
    )
    
    ai_response_message = response["messages"][-1]
    ai_response_content = ai_response_message.content

    ChatMessage.objects.create(
        session=chat_session, role='assistant', content=ai_response_content
    )

    token_usage = token_callback.get_token_usage()

    return ai_response_content, token_usage

