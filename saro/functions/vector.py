from langchain_community.vectorstores import FAISS
import os
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

import environ
env = environ.Env()

def load_doc_index(md_docs):

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(md_docs)

    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("AI_KEY"))
    vectorstore = FAISS.from_documents(chunks, embeddings)

    return vectorstore

# Helper to build a vector store from a string
def build_vectorstore_from_string(raw_content: str):
    """
    Build and return a FAISS vector store from a single large text string.
    """
    try:
        # Split the text into chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        # Wrap raw_content in a pseudo-document object
        docs = [Document(page_content=raw_content, metadata={})]
        chunks = splitter.split_documents(docs)
        # Create embeddings and vector store
        embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("AI_KEY"))
        vectorstore = FAISS.from_documents(chunks, embeddings)
        return vectorstore
    except Exception as e:
        print(f"Error building vector store from string: {e}")
        return None


def retrieve_relevant_docs(vectorstore, user_query, top_k=3):
    try:
        docs = vectorstore.similarity_search(user_query, k=top_k)
        # print("DEBUG retrieve_relevant_docs: docs =", docs)
        results = []
        for doc in docs:
            if isinstance(doc, dict):
                print("DEBUG doc is dict with keys:", list(doc.keys()))
                # Prefer page_content, then content
                if "page_content" in doc:
                    results.append(doc["page_content"])
                    continue
                if "content" in doc:
                    results.append(doc["content"])
                    continue
            # If it's a langchain Document, use its attribute
            if hasattr(doc, "page_content"):
                results.append(doc.page_content)
            else:
                # Fallback for unexpected types
                results.append(str(doc))
        return "\n\n".join(results)
    except Exception as e:
        print(f"Error retrieving relevant documents: {e}")
        return None