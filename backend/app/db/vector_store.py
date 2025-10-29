# app/db/vector_store.py
import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path="./chroma_memory")

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

def get_user_collection(user_id: str):
    return client.get_or_create_collection(
        name=f"user_{user_id}",
        embedding_function=embedding_fn
    )

def add_memory(user_id: str, text: str, metadata: dict):
    collection = get_user_collection(user_id)

    try:
        existing = collection.query(query_texts=[text], n_results=1)
        docs = existing.get("documents", [[]])[0]
        if docs:
            if text in docs[0] or docs[0] == text:
                return
    except Exception:
        pass

    doc_id = f"{user_id}_{metadata.get('turn_id', 0)}"
    collection.add(
        ids=[doc_id],
        documents=[text],
        metadatas=[metadata]
    )

def retrieve_memories(user_id: str, query: str, top_k: int = 3):
    collection = get_user_collection(user_id)
    results = collection.query(query_texts=[query], n_results=top_k)
    return results.get("documents", [[]])[0]
