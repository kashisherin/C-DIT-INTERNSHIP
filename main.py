from fastapi import FastAPI, HTTPException, UploadFile, Form, Query, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
import mimetypes
from fastapi.responses import FileResponse
import rag
import scraper
import grievance
import database 
import official_assistant
import os
import shutil
from pathlib import Path
import official_auth
import database_management_auth as database_management_auth

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
# Initialize grievance database and department storage.
database.init_db()

# ============================================================
# OFFICIAL AUTHENTICATION
# ============================================================

OFFICIAL_COOKIE_SECURE = (
    os.getenv("OFFICIAL_COOKIE_SECURE", "false").lower() == "true"
)


class OfficialLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)


def require_official(request: Request):
    """Require a valid official session."""

    token = request.cookies.get(official_auth.COOKIE_NAME)

    username = official_auth.validate_session_token(token)

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Official login required. Please sign in."
        )

    return username


DATABASE_MANAGEMENT_COOKIE_SECURE = (
    os.getenv("OFFICIAL_COOKIE_SECURE", "false").lower() == "true"
)
DATABASE_MANAGEMENT_COOKIE_PATH = "/api/official/database"


def require_database_management(request: Request):
    """Require the separate, short-lived Database Management session."""
    token = request.cookies.get(database_management_auth.COOKIE_NAME)
    username = database_management_auth.validate_session_token(token)

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Separate Database Management login required."
        )
    return username


def require_database_management_action(security_password: str):
    """Verify the separate action password on every edit/delete request."""
    if not database_management_auth.verify_action_password(security_password):
        raise HTTPException(
            status_code=403,
            detail="The separate edit/delete security password is incorrect."
        )


@app.post("/official/login")
def official_login(
    request: OfficialLoginRequest,
    response: Response
):
    if not official_auth.verify_credentials(
        request.username,
        request.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )

    token = official_auth.create_session_token(
        request.username
    )

    response.set_cookie(
        key=official_auth.COOKIE_NAME,
        value=token,
        max_age=official_auth.SESSION_DURATION_SECONDS,
        httponly=True,
        secure=OFFICIAL_COOKIE_SECURE,
        samesite="lax",
        path="/"
    )

    return {
        "authenticated": True,
        "username": request.username
    }


@app.get("/official/session")
def official_session(
    username: str = Depends(require_official)
):
    return {
        "authenticated": True,
        "username": username
    }


@app.post("/official/logout")
def official_logout(response: Response):
    response.delete_cookie(
        key=official_auth.COOKIE_NAME,
        path="/",
        httponly=True,
        secure=OFFICIAL_COOKIE_SECURE,
        samesite="lax"
    )
    response.delete_cookie(
        key=database_management_auth.COOKIE_NAME,
        path=DATABASE_MANAGEMENT_COOKIE_PATH,
        httponly=True,
        secure=DATABASE_MANAGEMENT_COOKIE_SECURE,
        samesite="strict"
    )

    return {
        "authenticated": False,
        "message": "Logged out successfully."
    }


# ============================================================
# 2. CORS CONFIGURATION
# ============================================================

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
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

class OfficialHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]

    content: str = Field(
        min_length=1,
        max_length=4000
    )


class OfficialChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=12000
    )

    history: list[OfficialHistoryMessage] = Field(
        default_factory=list,
        max_length=10
    )

class GrievanceStatusRequest(BaseModel):
    status: str = Field(
        min_length=1,
        max_length=30
    )
    security_password: str = Field(min_length=1, max_length=256)


class DatabaseManagementLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=256)


class ManagementGrievanceUpdateRequest(BaseModel):
    citizen_name: str | None = Field(default=None, max_length=300)
    summary: str = Field(min_length=1, max_length=20000)
    description: str = Field(min_length=1, max_length=50000)
    department_reason: str | None = Field(default=None, max_length=5000)
    status: str = Field(min_length=1, max_length=30)
    security_password: str = Field(min_length=1, max_length=256)


class ManagementDeleteSelectedRequest(BaseModel):
    grievance_ids: list[str] = Field(min_length=1, max_length=500)
    security_password: str = Field(min_length=1, max_length=256)


class ManagementDeleteFilteredRequest(BaseModel):
    department_code: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=30)
    date_from: str | None = Field(default=None, max_length=10)
    date_to: str | None = Field(default=None, max_length=10)
    security_password: str = Field(min_length=1, max_length=256)


class ManagementClearAllRequest(BaseModel):
    confirmation: str = Field(min_length=1, max_length=50)
    security_password: str = Field(min_length=1, max_length=256)

# ============================================================
# SEPARATE DATABASE MANAGEMENT AUTHENTICATION
# ============================================================


@app.post(
    "/official/database/access/login",
    dependencies=[Depends(require_official)]
)
def database_management_login(
    request: DatabaseManagementLoginRequest,
    response: Response
):
    if not database_management_auth.is_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Database Management credentials are not configured. "
                "Run database_management_auth.py and add its values to .env."
            )
        )

    if not database_management_auth.verify_login(
        request.username,
        request.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Database Management username or password."
        )

    token = database_management_auth.create_session_token(request.username)
    response.set_cookie(
        key=database_management_auth.COOKIE_NAME,
        value=token,
        max_age=database_management_auth.SESSION_DURATION_SECONDS,
        httponly=True,
        secure=DATABASE_MANAGEMENT_COOKIE_SECURE,
        samesite="strict",
        path=DATABASE_MANAGEMENT_COOKIE_PATH
    )

    return {
        "authenticated": True,
        "username": request.username,
        "expires_in": database_management_auth.SESSION_DURATION_SECONDS
    }


@app.get(
    "/official/database/access/session",
    dependencies=[Depends(require_official), Depends(require_database_management)]
)
def database_management_session():
    return {"authenticated": True}


@app.post(
    "/official/database/access/logout",
    dependencies=[Depends(require_official)]
)
def database_management_logout(response: Response):
    response.delete_cookie(
        key=database_management_auth.COOKIE_NAME,
        path=DATABASE_MANAGEMENT_COOKIE_PATH,
        httponly=True,
        secure=DATABASE_MANAGEMENT_COOKIE_SECURE,
        samesite="strict"
    )
    return {"authenticated": False, "message": "Database Management locked."}


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

    # Register the grievance in the central database.
    try:
        registration = database.register_grievance(
            department_code=result.department,
            original_filename=filename,
            document_bytes=data,
            summary=result.summary,
            description=result.description,
            department_reason=result.department_reason,
            citizen_name=result.citizen_name,
            original_language="unknown",
            response_language=language.lower()
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Grievance registration error: {error}"
        ) from error


    # Return analysis and registration details.
    return grievance.GrievanceResult(
        summary=result.summary,
        description=result.description,
        department=result.department,
        department_name=name,
        department_reason=result.department_reason,
        pages_read=len(images),
        citizen_name=result.citizen_name,
        grievance_id=registration["grievance_id"],
        department_slot=registration["department_slot"],
        status=registration["status"]
    )

# ============================================================
# 12. OFFICIAL GRIEVANCE MANAGEMENT API
# ============================================================


# ------------------------------------------------------------
# 12.1 Total registered grievances
# ------------------------------------------------------------

@app.get(
    "/official/grievances/summary",
    dependencies=[Depends(require_official)]
)
def official_grievance_summary():
    try:
        return database.get_grievance_counts()

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve grievance counts: {error}"
        ) from error


# ------------------------------------------------------------
# 12.2 List all grievances or filter by department
# ------------------------------------------------------------

@app.get(
    "/official/grievances",
    dependencies=[Depends(require_official)]
)
def official_list_grievances(
    department: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):

    try:
        records = database.list_grievances(
            department_code=department,
            limit=limit,
            offset=offset
        )

        return {
            "count": len(records),
            "limit": limit,
            "offset": offset,
            "grievances": records
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve grievances: {error}"
        ) from error


# ------------------------------------------------------------
# 12.3 Search by citizen name or grievance ID
# ------------------------------------------------------------

@app.get(
    "/official/grievances/search",
    dependencies=[Depends(require_official)]
)
def official_search_grievances(
    q: str = Query(min_length=1, max_length=200),
    department: str | None = None,
    limit: int = Query(default=50, ge=1, le=500)
):

    try:
        records = database.search_grievances(
            query=q,
            department_code=department,
            limit=limit
        )

        return {
            "query": q,
            "count": len(records),
            "grievances": records
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Grievance search failed: {error}"
        ) from error


# ------------------------------------------------------------
# 12.4 Retrieve a grievance using its unique ID
# ------------------------------------------------------------

@app.get(
    "/official/grievances/id/{grievance_id}",
    dependencies=[Depends(require_official)]
)
def official_get_grievance(grievance_id: str):

    try:
        record = database.get_grievance_by_id(
            grievance_id
        )

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Grievance not found."
            )

        # Do not expose the server's internal file path.
        record.pop("document_path", None)

        return record

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve grievance: {error}"
        ) from error


# ------------------------------------------------------------
# 12.5 Retrieve a grievance using department and slot number
# ------------------------------------------------------------

@app.get(
    "/official/grievances/department/{department_code}/slot/{department_slot}",
    dependencies=[Depends(require_official)]
)
def official_get_grievance_by_slot(
    department_code: str,
    department_slot: int
):

    try:
        record = database.get_grievance_by_department_slot(
            department_code,
            department_slot
        )

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="No grievance found for this department and slot."
            )

        # Do not expose the server's internal file path.
        record.pop("document_path", None)

        return record

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve grievance: {error}"
        ) from error


# ------------------------------------------------------------
# 12.6 Download the original grievance document
# ------------------------------------------------------------

@app.get(
    "/official/grievances/id/{grievance_id}/document",
    dependencies=[Depends(require_official)]
)
def official_get_grievance_document(grievance_id: str):

    try:
        # Retrieve the database record.
        record = database.get_grievance_by_id(
            grievance_id
        )

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Grievance not found."
            )

        # Retrieve the stored document path.
        relative_path = record.get("document_path")

        if not relative_path:
            raise HTTPException(
                status_code=404,
                detail="No document is associated with this grievance."
            )

        # Resolve the actual file location.
        storage_root = database.DEPARTMENT_STORAGE.resolve()

        document_path = (
            database.BASE_DIR / relative_path
        ).resolve()

        # Ensure the requested file belongs to grievance storage.
        if not document_path.is_relative_to(storage_root):
            raise HTTPException(
                status_code=403,
                detail="Access to this document path is not allowed."
            )

        if not document_path.is_file():
            raise HTTPException(
                status_code=404,
                detail="Original grievance document not found."
            )

        # Identify the file type.
        media_type, _ = mimetypes.guess_type(
            str(document_path)
        )

        # Return the original document.
        return FileResponse(
            path=document_path,
            media_type=media_type or "application/octet-stream",
            filename=document_path.name
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve original document: {error}"
        ) from error


# ============================================================
# 13. OFFICIAL AI CHATBOT
# ============================================================

@app.post(
    "/official/chat",
    dependencies=[Depends(require_official)]
)
def official_chat(request: OfficialChatRequest):

    try:
        # Convert conversation history into the format
        # expected by official_assistant.py.
        history = [
            message.model_dump()
            for message in request.history
        ]

        # Understand the question and retrieve real records.
        result = official_assistant.answer_official_question(
            question=request.question,
            history=history
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Official assistant error: {error}"
        ) from error


# ============================================================
# 14. UPDATE GRIEVANCE STATUS
# ============================================================

@app.patch(
    "/official/grievances/id/{grievance_id}/status",
    dependencies=[Depends(require_official)]
)
def official_update_grievance_status(
    grievance_id: str,
    request: GrievanceStatusRequest
):
    require_database_management_action(request.security_password)
    try:
        record = database.update_grievance_status(
            grievance_id=grievance_id,
            new_status=request.status
        )

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Grievance not found."
            )

        return {
            "message": "Grievance status updated successfully.",
            "grievance_id": record["grievance_id"],
            "department_code": record["department_code"],
            "department_slot": record["department_slot"],
            "status": record["status"],
            "updated_at": record["updated_at"]
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Status update failed: {error}"
        ) from error

# ============================================================
# 15. OFFICIAL DATABASE MANAGEMENT
# ============================================================


@app.get(
    "/official/database/summary",
    dependencies=[Depends(require_official), Depends(require_database_management)]
)
def official_database_summary():
    try:
        return database.get_grievance_counts()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not retrieve database summary: {error}"
        ) from error


@app.get(
    "/official/database/grievances",
    dependencies=[Depends(require_official), Depends(require_database_management)]
)
def official_database_list_grievances(
    department_code: str | None = None,
    status: str | None = None,
    search: str | None = Query(default=None, max_length=200),
    date_from: str | None = Query(default=None, max_length=10),
    date_to: str | None = Query(default=None, max_length=10),
    limit: int = Query(default=500, ge=1, le=500),
    offset: int = Query(default=0, ge=0)
):
    try:
        records = database.list_management_grievances(
            department_code=department_code,
            status=status,
            search=search,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset
        )
        return {"count": len(records), "grievances": records}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not list managed grievances: {error}"
        ) from error


@app.patch(
    "/official/database/grievances/{grievance_id}",
    dependencies=[Depends(require_official), Depends(require_database_management)]
)
def official_database_update_grievance(
    grievance_id: str,
    request: ManagementGrievanceUpdateRequest
):
    require_database_management_action(request.security_password)
    try:
        record = database.update_grievance_record(
            grievance_id=grievance_id,
            citizen_name=request.citizen_name,
            summary=request.summary,
            description=request.description,
            department_reason=request.department_reason,
            status=request.status
        )
        if record is None:
            raise HTTPException(status_code=404, detail="Grievance not found.")
        record.pop("document_path", None)
        return {"message": "Grievance updated successfully.", "record": record}
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not update grievance: {error}"
        ) from error


@app.post(
    "/official/database/grievances/delete-selected",
    dependencies=[Depends(require_official), Depends(require_database_management)]
)
def official_database_delete_selected(
    request: ManagementDeleteSelectedRequest
):
    require_database_management_action(request.security_password)
    try:
        result = database.delete_grievances_by_ids(request.grievance_ids)
        return {"message": "Selected grievances deleted.", **result}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not delete selected grievances: {error}"
        ) from error


@app.post(
    "/official/database/grievances/delete-filtered",
    dependencies=[Depends(require_official), Depends(require_database_management)]
)
def official_database_delete_filtered(
    request: ManagementDeleteFilteredRequest
):
    require_database_management_action(request.security_password)
    if not any((
        request.department_code,
        request.status,
        request.date_from,
        request.date_to
    )):
        raise HTTPException(
            status_code=400,
            detail="Choose a department, status or date range before filtered deletion."
        )

    try:
        result = database.delete_grievances_by_filters(
            department_code=request.department_code,
            status=request.status,
            date_from=request.date_from,
            date_to=request.date_to
        )
        return {"message": "Filtered grievances deleted.", **result}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not delete filtered grievances: {error}"
        ) from error


@app.post(
    "/official/database/clear-all",
    dependencies=[Depends(require_official), Depends(require_database_management)]
)
def official_database_clear_all(request: ManagementClearAllRequest):
    require_database_management_action(request.security_password)
    if request.confirmation != "DELETE ALL GRIEVANCES":
        raise HTTPException(
            status_code=400,
            detail="Type DELETE ALL GRIEVANCES exactly to confirm."
        )

    try:
        # Delete all database rows and document folders referenced by them.
        result = database.clear_all_grievances()

        # Also remove orphaned items that may remain inside the dedicated
        # department grievance folders, while keeping each department folder.
        storage_root = Path(database.DEPARTMENT_STORAGE).resolve()
        storage_root.mkdir(parents=True, exist_ok=True)
        orphan_items_removed = 0
        cleanup_errors = list(result.get("cleanup_errors", []))

        for department in database.DEPARTMENTS:
            department_folder = storage_root / department

            if department_folder.is_symlink():
                cleanup_errors.append(
                    f"Skipped symbolic-link department folder: {department}"
                )
                continue

            department_folder.mkdir(parents=True, exist_ok=True)

            for item in department_folder.iterdir():
                try:
                    if item.is_symlink() or item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                    orphan_items_removed += 1
                except OSError as error:
                    cleanup_errors.append(f"{item.name}: {error}")

        result["orphan_items_removed"] = orphan_items_removed
        result["cleanup_errors"] = cleanup_errors
        result["message"] = "All grievance database records have been cleared."
        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not clear the grievance database: {error}"
        ) from error

