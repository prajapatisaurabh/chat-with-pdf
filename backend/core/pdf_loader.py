# backend/core/pdf_loader.py
import os
from typing import List
from pypdf import PdfReader


def read_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    texts = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        texts.append(txt)
    return "\n".join(texts)

def chunk_text(text: str, chunk_size: int = 1200, chunk_overlap: int = 200) -> List[str]:
    # Simple recursive char splitter
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        # try to break on sentence end if possible
        last_period = chunk.rfind(". ")
        if last_period != -1 and end != text_len and last_period > chunk_size // 2:
            end = start + last_period + 2
            chunk = text[start:end]
        chunks.append(chunk.strip())
        start = max(end - chunk_overlap, 0) if end < text_len else end
    # remove empties
    return [c for c in chunks if c]