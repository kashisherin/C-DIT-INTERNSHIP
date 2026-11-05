import io
from typing import Literal

import ollama
import pypdfium2 as pdfium

from PIL import Image
from pydantic import BaseModel


# ---------- Settings ----------

VISION_MODEL = "gemma4:e4b"  # Must be a model that can read images

MAX_PAGES = 3  # Read at most this many PDF pages
MAX_SIDE = 1600  # Shrink big photos to this many pixels (long side)


# ---------- 1. The departments a grievance can be routed to ----------

# Code -> (full name, what it handles).
# Edit to match the real routing rules.

DEPARTMENTS = {
    "KWA": (
        "Kerala Water Authority",
        "drinking water supply, broken or leaking pipes, water bills, sewerage"
    ),

    "KSEB": (
        "Kerala State Electricity Board",
        "power cuts, low voltage, transformers, electric lines and poles, "
        "electricity bills"
    ),

    "PWD": (
        "Public Works Department",
        "state highways and major roads, potholes, bridges, government buildings"
    ),

    "LSGD": (
        "Local Self Government Department",
        "waste collection, street lights, drains, panchayat or municipal roads, "
        "building permits, birth and death certificates"
    ),

    "REVENUE": (
        "Revenue Department",
        "land records, land tax, income or caste certificates, disaster relief"
    ),

    "POLICE": (
        "Kerala Police",
        "crime, threats, harassment, public safety, traffic law enforcement"
    ),

    "HEALTH": (
        "Health Department",
        "government hospitals, doctors, medicines, disease outbreaks"
    ),

    "EDUCATION": (
        "General Education Department",
        "government schools, teachers, admissions, scholarships"
    ),

    "CIVIL_SUPPLIES": (
        "Civil Supplies Department",
        "ration cards, ration shops, food grain supply"
    ),

    "SOCIAL_JUSTICE": (
        "Social Justice Department",
        "welfare pensions, disability, elderly and widow support"
    ),

    "TRANSPORT": (
        "Transport Department / KSRTC",
        "KSRTC buses, bus routes, driving licences, vehicle registration"
    ),

    "OTHER": (
        "Other / manual review",
        "anything that does not clearly fit the departments above"
    ),
}


# ---------- 2. Department code type ----------

DepartmentCode = Literal[
    "KWA",
    "KSEB",
    "PWD",
    "LSGD",
    "REVENUE",
    "POLICE",
    "HEALTH",
    "EDUCATION",
    "CIVIL_SUPPLIES",
    "SOCIAL_JUSTICE",
    "TRANSPORT",
    "OTHER"
]
# ---------- 2. The exact shape we want the model to answer in ----------

class GrievanceAnalysis(BaseModel):
    summary: str  # 2-3 sentences for the citizen and the official

    description: str  # Full details in clear English

    department: DepartmentCode  # Must be one of the codes above

    department_reason: str  # One sentence: why this department

# ---------- 3. Turn the uploaded file into images ----------

def to_png(image):
    image = image.convert("RGB")

    image.thumbnail(
        (MAX_SIDE, MAX_SIDE)
    )  # Keeps the shape, only shrinks

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    return buffer.getvalue()


def file_to_images(data, filename):
    if filename.lower().endswith(".pdf"):
        pdf = pdfium.PdfDocument(data)

        page_count = min(
            len(pdf),
            MAX_PAGES
        )

        pages = [
            pdf[i].render(scale=2).to_pil()
            for i in range(page_count)
        ]

        return [
            to_png(page)
            for page in pages
        ]

    return [
        to_png(
            Image.open(io.BytesIO(data))
        )
    ]
# ---------- 4. Ask the model to read and classify the grievance ----------

def build_prompt():
    department_lines = "\n".join(
        f"- {code}: {name} - handles {handles}"
        for code, (name, handles) in DEPARTMENTS.items()
    )

    return f"""You assist the Chief Minister's Public Grievance Cell, Kerala.

The image(s) show a grievance letter from a citizen. It is usually handwritten,
in English or Malayalam.

1. Read the letter carefully.

2. summary: 2 or 3 short sentences in English: who is complaining, what the problem
   is, and where.

3. description: the full grievance in clear English, keeping every important detail:
   names, house or ward numbers, places, dates, how long the problem has lasted,
   what was already tried, and what the citizen is asking for. Do not invent details.
   Write [unclear] for words you cannot read.

4. department: choose the ONE department code that should handle it:
{department_lines}

5. department_reason: one sentence explaining your choice.

Answer only in the requested JSON format."""


def analyze_grievance(images):
    response = ollama.chat(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": build_prompt(),
                "images": images
            }
        ],
        format=GrievanceAnalysis.model_json_schema(),  # Force this JSON shape
        options={
            "temperature": 0  # Same input -> same answer
        },
    )

    return GrievanceAnalysis.model_validate_json(
        response["message"]["content"]
    )
# ---------- Grievances ----------

ALLOWED_TYPES = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".pdf"
)

MAX_UPLOAD_MB = 10


class GrievanceResult(BaseModel):
    summary: str
    description: str
    department: str
    department_name: str
    department_reason: str
    pages_read: int


