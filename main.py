from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import rag
import scraper
import grievance


# ============================================================
# 1. APPLICATION CONFIGURATION
# ============================================================

app = FastAPI(
    title="Multilingual RAG AI Application",
    description=(
        "Multilingual document question answering using "
        "MIRA-IndicLID, local EmbeddingGemma and Google Gemma 4."
    ),
    version="2.1.0"
)


# ============================================================
# 2. CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 3. REQUEST AND RESPONSE MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=12000
    )


class ChatResponse(BaseModel):
    reply: str


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=12000
    )
    response_language: str = Field(
        default="en",
        pattern="^(en|ml)$"
    )


class Source(BaseModel):
    source: str
    text: str
    distance: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


class FetchRequest(BaseModel):
    url: str


class LanguageRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=12000
    )


# ============================================================
# 4. HEALTH CHECK
# ============================================================

@app.get("/")
def health_check():

    try:
        chunk_count = rag.get_collection().count()
        database_status = "ok"

    except Exception as error:
        chunk_count = 0
        database_status = f"error: {error}"

    return {
        "status": "ok",
        "database_status": database_status,
        "language_detector": "MIRA-IndicLID",
        "language_model_path": str(rag.MIRA_MODEL_PATH),
        "chat_model": rag.CHAT_MODEL,
        "vision_model": grievance.VISION_MODEL,
        "embed_model": rag.EMBED_MODEL,
        "chunks_in_database": chunk_count,
    }


# ============================================================
# 5. LANGUAGE DETECTION
# ============================================================

@app.post("/detect-language")
def detect_language(request: LanguageRequest):

    try:
        return rag.detect_language(request.text)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Language detection error: {error}"
        ) from error


# ============================================================
# 6. GENERAL CHAT
# ============================================================

# This endpoint does not use indexed documents.
# It is intended for normal conversational questions.

@app.post(
    "/chat",
    response_model=ChatResponse
)
def chat(request: ChatRequest):

    try:
        reply = rag.chat_without_documents(
            request.message
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Chat model error: {error}"
        ) from error

    return ChatResponse(
        reply=reply
    )


# ============================================================
# 7. FETCH A WEB PAGE AND INDEX IT
# ============================================================

@app.post("/fetch")
def fetch(request: FetchRequest):

    if not request.url.startswith(
        ("http://", "https://")
    ):
        raise HTTPException(
            status_code=400,
            detail="URL must start with http:// or https://"
        )

    try:
        page = scraper.fetch_and_save(
            request.url
        )

        page["chunks_indexed"] = rag.index_file(
            page["file"]
        )

        return page

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Fetch/index error: {error}"
        ) from error


# ============================================================
# 8. LIST INDEXED SOURCES
# ============================================================

@app.get("/sources")
def sources():

    try:
        return rag.list_sources()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not list sources: {error}"
        ) from error


# ============================================================
# 9. INGEST DOCUMENTS
# ============================================================

@app.post("/ingest")
def ingest():

    try:
        return rag.index_documents()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Ingest error: {error}"
        ) from error


# ============================================================
# 10. RAG QUESTION ANSWERING
# ============================================================

@app.post(
    "/ask",
    response_model=AskResponse
)
def ask(request: AskRequest):

    # AskRequest validates the language as "en" or "ml".
    try:
        answer, chunks = rag.answer_question(
            request.question,
            response_language=request.response_language
        )

        return AskResponse(
            answer=answer,
            sources=chunks
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"RAG error: {error}"
        ) from error


# ============================================================
# 11. GRIEVANCE MANAGEMENT
# ============================================================

ALLOWED_TYPES = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".pdf"
)

MAX_UPLOAD_MB = 10


# ------------------------------------------------------------
# 11.1 List departments
# ------------------------------------------------------------

@app.get("/departments")
def departments():

    return [
        {
            "code": code,
            "name": name
        }
        for code, (name, _handles)
        in grievance.DEPARTMENTS.items()
    ]


# ------------------------------------------------------------
# 11.2 Process uploaded grievance
# ------------------------------------------------------------

@app.post(
    "/grievance/process",
    response_model=grievance.GrievanceResult
)
def process_grievance(
    file: UploadFile,
    language: str = Form("en")
):

    filename = file.filename or ""

    # Validate selected output language.
    supported_languages = {
        "en": "English",
        "ml": "Malayalam"
    }

    output_language = supported_languages.get(
        language.strip().lower()
    )

    if output_language is None:
        raise HTTPException(
            status_code=400,
            detail="Unsupported language. Use 'en' or 'ml'."
        )

    # Validate file extension.
    if not filename.lower().endswith(ALLOWED_TYPES):
        raise HTTPException(
            status_code=400,
            detail="Upload a JPG, JPEG, PNG, WEBP or PDF file."
        )

    # Read uploaded file.
    try:
        data = file.file.read()
    finally:
        file.file.close()

    if not data:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    # Validate file size.
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File is larger than {MAX_UPLOAD_MB} MB."
        )

    # Convert document into images.
    try:
        images = grievance.file_to_images(
            data,
            filename
        )

        if not images:
            raise ValueError(
                "No readable pages or images were found."
            )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Could not open the file: {error}"
        ) from error

    # Analyse grievance using Google Gemma 4.
    try:
        result = grievance.analyze_grievance(
            images,
            output_language=output_language
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Grievance analysis error: {error}"
        ) from error

    # Get department details.
    name, _handles = grievance.DEPARTMENTS[
        result.department
    ]

    # Return grievance analysis.
    return grievance.GrievanceResult(
        summary=result.summary,
        description=result.description,
        department=result.department,
        department_name=name,
        department_reason=result.department_reason,
        pages_read=len(images)
    )
