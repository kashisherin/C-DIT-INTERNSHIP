from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import ollama
import rag
import scraper


app = FastAPI(title="RAG AI Application")


# ---------- CORS Configuration ----------

# Allow the React app (running on port 5173) to call this API

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Request and response shapes ----------

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


class AskRequest(BaseModel):
    question: str


class Source(BaseModel):
    source: str
    text: str
    distance: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


class FetchRequest(BaseModel):
    url: str


# ---------- Endpoints ----------

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "chat_model": rag.CHAT_MODEL,
        "embed_model": rag.EMBED_MODEL,
        "chunks_in_database": rag.get_collection().count(),
    }


# Plain chat, no documents. Keep it to compare.

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        response = ollama.chat(
            model=rag.CHAT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": request.message
                }
            ],
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama error: {error}"
        )

    return ChatResponse(
        reply=response["message"]["content"]
    )


# Download a web page, save it as Markdown, and add it to the database.

@app.post("/fetch")
def fetch(request: FetchRequest):
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="URL must start with http:// or https://"
        )

    try:
        page = scraper.fetch_and_save(request.url)

        page["chunks_indexed"] = rag.index_file(
            page["file"]
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Fetch error: {error}"
        )

    return page


# List what is in the database.

@app.get("/sources")
def sources():
    return rag.list_sources()


# Rebuild the database from every file in the documents folder.

@app.post("/ingest")
def ingest():
    try:
        return rag.index_documents()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ingest error: {error}"
        )


# Answer a question using the documents (this is RAG).

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        answer, chunks = rag.answer_question(
            request.question
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"RAG error: {error}"
        )

    return AskResponse(
        answer=answer,
        sources=chunks
    )