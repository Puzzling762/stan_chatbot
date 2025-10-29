# app/db/vector_store.py
import chromadb
from chromadb.utils import embedding_functions

# initialize persistent DB (you can change path if needed)
client = chromadb.PersistentClient(path="./chroma_memory")

# use SentenceTransformers for embeddings
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# get or create a collection
def get_user_collection(user_id: str):
    return client.get_or_create_collection(
        name=f"user_{user_id}",
        embedding_function=embedding_fn
    )

# app/db/vector_store.py  (portion to replace add_memory)
def add_memory(user_id: str, text: str, metadata: dict):
    collection = get_user_collection(user_id)

    # Quick duplicate check: query top 1 for identical text
    try:
        existing = collection.query(query_texts=[text], n_results=1)
        docs = existing.get("documents", [[]])[0]
        if docs:
            # If identical or very similar text is found, skip adding
            if text in docs[0] or docs[0] == text:
                return
    except Exception:
        # ignore query errors and proceed to add - safe fallback
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