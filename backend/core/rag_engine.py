# backend/core/rag_engine.py
import os
from typing import Dict, List
from .vector_store import LocalVectorStore
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/openai/")
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash")
TOP_K = int(os.getenv("TOP_K", 4))

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set in environment.")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"

)

class RAGEngine:
    def __init__(self, persist_dir: str, embedding_model: str):
        self.store = LocalVectorStore(persist_dir=persist_dir, embedding_model=embedding_model)

    def index_pdf(self, pdf_id: str, chunks: List[str]):
        self.store.upsert(pdf_id, chunks)

    def retrieve(self, pdf_id: str, question: str, top_k: int = TOP_K) -> List[str]:
        pairs = self.store.query(pdf_id, question, top_k=top_k)
        return [doc for doc, _score in pairs]

    def generate(self, question: str, contexts: List[str]) -> str:
        system_prompt = (
            "You are a helpful assistant that answers questions using the provided PDF context. "
            "If the answer is not in the context, say you don't know. Cite relevant chunks as bullet points."
        )
        context_block = "\n\n".join([f"[Chunk {i+1}]\n{c}" for i, c in enumerate(contexts)])
        user_prompt = f"Question: {question}\n\nContext:\n{context_block}"

        resp = client.chat.completions.create(
          model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content