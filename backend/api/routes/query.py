# backend/api/routes/query.py
import os
from typing import Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from ...core.rag_engine import RAGEngine

load_dotenv()

PERSIST_DIR = os.getenv("PERSIST_DIR", "backend/storage/vectors")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
TOP_K = int(os.getenv("TOP_K", 4))

rag = RAGEngine(persist_dir=PERSIST_DIR, embedding_model=EMBED_MODEL)

router = APIRouter()


class AskBody(BaseModel):
    pdf_id: str
    question: str

class AskResponse(BaseModel):
    answer: str
    contexts: List[str]

@router.post("/ask", response_model=AskResponse)
async def ask(body: AskBody):
    contexts = rag.retrieve(body.pdf_id, body.question, top_k=TOP_K)
    if not contexts:
        raise HTTPException(status_code=404, detail="No context found for this PDF id. Re-upload the PDF.")

    answer = rag.generate(body.question, contexts)
    return AskResponse(answer=answer, contexts=contexts)
