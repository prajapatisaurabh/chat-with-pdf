# backend/core/vector_store.py
import os
from typing import List, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class LocalVectorStore:
    def __init__(self, persist_dir: str, embedding_model: str = "all-MiniLM-L6-v2"):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.Client(Settings(persist_directory=persist_dir))
        self.embedder = SentenceTransformer(embedding_model)

    def _col_name(self, pdf_id: str) -> str:
        return f"pdf_{pdf_id}"

    def upsert(self, pdf_id: str, chunks: List[str]):
        col = self.client.get_or_create_collection(self._col_name(pdf_id))
        embeddings = self.embedder.encode(chunks, normalize_embeddings=True).tolist()
        ids = [f"{pdf_id}_{i}" for i in range(len(chunks))]
        col.upsert(documents=chunks, embeddings=embeddings, ids=ids)

    def query(self, pdf_id: str, text: str, top_k: int = 4) -> List[Tuple[str, float]]:
        col = self.client.get_or_create_collection(self._col_name(pdf_id))
        q_emb = self.embedder.encode([text], normalize_embeddings=True).tolist()
        res = col.query(query_embeddings=q_emb, n_results=top_k)
        docs = res.get("documents", [[]])[0]
        dists = res.get("distances", [[]])[0]
        # Convert cosine distance to similarity score (1 - dist) if needed
        out = list(zip(docs, [1 - d for d in dists]))
        return out

    def drop(self, pdf_id: str):
        name = self._col_name(pdf_id)
        try:
            self.client.delete_collection(name)
        except Exception:
            pass