import sys
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'data_traitement', '.env'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rag'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pipeline import ask

app = FastAPI(title="Ancient Rome RAG API")


class QueryRequest(BaseModel):
    question: str


class Source(BaseModel):
    source: str
    chapter: str
    section: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = ask(request.question)
    return result
