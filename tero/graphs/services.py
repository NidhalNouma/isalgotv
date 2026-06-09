from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

def build_vector_store_from_text(text: str, chunk_size: int = 1000, overlap: int = 100, vectorstore_path = "vector_index", embeddings = OpenAIEmbeddings(model="text-embedding-3-large")):
    """
    Splits the text and saves a FAISS vector index locally.
    """

    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    docs = splitter.create_documents([text])
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(vectorstore_path)

# cache variable at module level
_cached_vectorstores = {}

def retrieve_context_from_vector_store(user_question, vectorstore_path = "vector_index",  embeddings = OpenAIEmbeddings(model="text-embedding-3-large"), force_loading = False):
    """
    Loads the saved FAISS vector index.
    """

    global _cached_vectorstores
    if vectorstore_path not in _cached_vectorstores or force_loading == True:
        _cached_vectorstores[vectorstore_path] = FAISS.load_local(
            vectorstore_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
    
    vectorstore = _cached_vectorstores[vectorstore_path]
    retriever = vectorstore.as_retriever()

    retrieved_docs = retriever.invoke(user_question)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    return context

