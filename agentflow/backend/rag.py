import os, chromadb
from .openai_client import get_client

client = get_client()
MODEL = os.getenv("MODEL_NAME")

db = chromadb.Client()
col = db.get_or_create_collection("docs")

def add_doc(doc_id: str, text: str):
    emb = client.embeddings.create(model=MODEL, input=[text]).data[0].embedding
    col.add(ids=[doc_id], documents=[text], embeddings=[emb])

def retrieve(query: str, k: int = 4) -> str:
    q_emb = client.embeddings.create(model=MODEL, input=[query]).data[0].embedding
    res = col.query(query_embeddings=[q_emb], n_results=k)
    return "\n\n".join(res["documents"][0]) if res["documents"] else ""
