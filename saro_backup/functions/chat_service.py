from typing import List, Dict, Any, Union, Optional, Callable
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import HumanMessage, AIMessage, BaseMessage
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.callbacks import get_openai_callback
from langchain.callbacks.base import BaseCallbackHandler

class StreamHandler(BaseCallbackHandler):
    def __init__(self, token_callback: Callable[[str], None]):
        self.token_callback = token_callback

    def on_llm_new_token(self, token: str, **kwargs):
        self.token_callback(token)

class ChatService:
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        summary_model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.5,
        vectorstore_path: str = "vector_index"
    ):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.summary_llm = ChatOpenAI(model=summary_model_name, temperature=temperature, streaming=True)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.vectorstore_path = vectorstore_path
        self.retriever = None

    def build_vector_store_from_text(self, text: str, chunk_size: int = 1000, overlap: int = 100):
        """
        Splits the text and saves a FAISS vector index locally.
        """
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        docs = splitter.create_documents([text])
        vectorstore = FAISS.from_documents(docs, self.embeddings)
        vectorstore.save_local(self.vectorstore_path)

    def load_vector_store(self):
        """
        Loads the saved FAISS vector index.
        """
        vectorstore = FAISS.load_local(self.vectorstore_path, self.embeddings, allow_dangerous_deserialization=True)
        self.retriever = vectorstore.as_retriever()

    def generate_response(
        self,
        user_question: str,
        message_history: List[Dict[str, str]]
    ) -> Any:
        """
        Generates a response using memory + retrieved doc context.
        Returns result with token usage and cost.
        """
        if not self.retriever:
            self.load_vector_store()

        retrieved_docs = self.retriever.invoke(user_question)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        print(context)

        # Format history for LangChain
        formatted_history: List[BaseMessage] = []
        for msg in message_history:
            if msg["role"] == "user":
                formatted_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_history.append(AIMessage(content=msg["content"]))

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "You are Saro, a trading assistant. If the user asks a question, "
                    "Display images if they are relevant to the question and the context provided."
                    "you should answer it based on the context provided below.\n\nContext:\n{context}"
                ),
                HumanMessagePromptTemplate.from_template("{question}")
            ]
        )

        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=False,
            combine_docs_chain_kwargs={"prompt": prompt}
        )

        with get_openai_callback() as cb:
            result = qa_chain.invoke({
                "question": user_question,
                "chat_history": formatted_history,
                "context": context
            })

        return {
            "response": result.get("answer", ""),
            "prompt_tokens": cb.prompt_tokens,
            "completion_tokens": cb.completion_tokens,
            "total_tokens": cb.total_tokens,
            "total_cost": cb.total_cost
        }

    def summarize_conversation(self, message_history: List[Dict[str, str]]) -> str:
        """
        Summarizes a conversation using the LLM.
        """
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain

        # Flatten the conversation into a readable string
        history_text = ""
        for msg in message_history:
            role = msg["role"].capitalize()
            content = msg["content"]
            history_text += f"{role}: {content}\n"

        # Create a prompt to summarize the conversation
        prompt = PromptTemplate(
            input_variables=["history"],
            template=(
                "You are a helpful trading assistant. Summarize the following conversation:\n\n"
                "{history}\n\nSummary:"
            )
        )

        summary_chain = LLMChain(llm=self.summary_llm, prompt=prompt)
        return summary_chain.run({"history": history_text})
    
    def stream_response(
        self,
        user_question: str,
        message_history: List[Dict[str, str]]
    ):
        if not self.retriever:
            self.load_vector_store()

        retrieved_docs = self.retriever.invoke(user_question)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])

        formatted_history: List[BaseMessage] = []
        for msg in message_history:
            if msg["role"] == "user":
                formatted_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_history.append(AIMessage(content=msg["content"]))

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "You are Saro, a trading assistant. If the user asks a question, "
                    "Display images if they are relevant to the question and the context provided."
                    "you should answer it based on the context provided below.\n\nContext:\n{context}"
                ),
                HumanMessagePromptTemplate.from_template("{question}")
            ]
        )

        messages = prompt.format_prompt(context=context, question=user_question).to_messages()
        messages = formatted_history + messages  # Optionally prepend history

        # Streaming LLM
        def yield_token(token):
            yield token

        # Set up a generator for tokens
        def token_generator():
            tokens = []
            def callback(token):
                tokens.append(token)
                yield token
            handler = StreamHandler(callback)
            streaming_llm = ChatOpenAI(
                model=self.llm.model,
                temperature=self.llm.temperature,
                streaming=True,
                callbacks=[handler],
            )
            for chunk in streaming_llm.stream(messages):
                yield chunk.content

        # Return as generator
        return token_generator()