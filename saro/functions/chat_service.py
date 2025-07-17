from typing import List, Dict, Union
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import HumanMessage, AIMessage, BaseMessage
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.callbacks import get_openai_callback


import environ
env = environ.Env()


class ChatService:
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        summary_model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.0,
        vectorstore_path: str = "vector_index"
    ):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature, api_key=env("AI_KEY"))
        self.summary_llm = ChatOpenAI(model=summary_model_name, temperature=temperature, api_key=env("AI_KEY"))
        self.embeddings = OpenAIEmbeddings(api_key=env("AI_KEY"))
        self.vectorstore_path = vectorstore_path
        self.retriever = None

    def build_vector_store_from_text(self, text: str, chunk_size: int = 500, overlap: int = 50):
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
    ) -> Dict[str, Union[str, int, float]]:
        """
        Generates a response using memory + retrieved doc context.
        Returns result with token usage and cost.
        """
        if not self.retriever:
            self.load_vector_store()

        # Format history for LangChain
        formatted_history: List[BaseMessage] = []
        for msg in message_history:
            if msg["role"] == "user":
                formatted_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_history.append(AIMessage(content=msg["content"]))

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                "You are Saro, a trading assistant."
            ),
            HumanMessagePromptTemplate.from_template("Context:\n{context}\n\nQuestion:\n{question}")
        ])

        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=False,
            combine_docs_chain_kwargs={"prompt": prompt}
        )

        with get_openai_callback() as cb:
            result = qa_chain.invoke({
                "question": user_question,
                "chat_history": formatted_history
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