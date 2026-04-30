#backend/app/agent/tools/retriever.py
import os
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

def get_retriever():
    """
    Creates a retriever that connects to the existing Pinecone index.
    """
    # 1. Initialize the same embedding model used in ingest.py
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # 2. Connect to the VectorStore
    # 'text_key="text"' is crucial because it matches the metadata key in ingest.py
    vectorstore = PineconeVectorStore(
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        embedding=embeddings,
        text_key="text"
    )

    # 3. Return as a retriever
    # 'k=3' means it will grab the top 3 most relevant context snippets
    return vectorstore.as_retriever(search_kwargs={"k": 3})