# backend/api/routes/pdf.py
import os
import uuid
from typing import Dict
from fastapi import APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from ...core.pdf_loader import read_pdf_text, chunk_text
from ...core.rag_engine import RAGEngine

load_dotenv()

PDF_DIR = os.getenv("PDF_DIR", "backend/storage/pdfs")
PERSIST_DIR = os.getenv("PERSIST_DIR", "backend/storage/vectors")
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

os.makedirs(PDF_DIR, exist_ok=True)

rag = RAGEngine(persist_dir=PERSIST_DIR, embedding_model=EMBED_MODEL)

router = APIRouter()


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)) -> Dict[str, str]:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    pdf_id = str(uuid.uuid4())[:8]
    out_path = os.path.join(PDF_DIR, f"{pdf_id}.pdf")

    with open(out_path, "wb") as f:
        f.write(await file.read())

    text = read_pdf_text(out_path)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from this PDF.")

    chunks = chunk_text(text)
    rag.index_pdf(pdf_id, chunks)

    return {"pdf_id": pdf_id, "chunks": str(len(chunks))}


@router.delete("/{pdf_id}")
async def delete_pdf(pdf_id: str):
    # Delete raw file
    path = os.path.join(PDF_DIR, f"{pdf_id}.pdf")
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
    # Delete vectors
    rag.store.drop(pdf_id)
    return {"deleted": pdf_id}