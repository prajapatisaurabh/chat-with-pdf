# backend/api/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Chat with Your PDF API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes import pdf, query  # noqa: E402

app.include_router(pdf.router, prefix="/pdf", tags=["pdf"])
app.include_router(query.router, prefix="/query", tags=["query"])


@app.get("/")
def health():
    return {"status": "ok"}