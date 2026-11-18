"""
Official Grievance Assistant

Uses Gemma 4 to understand officials' questions.
Uses SQLite to retrieve the actual grievance records.

The AI does not generate SQL queries or invent database records.
"""

import json
import re
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

import database


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ============================================================
# 1. QUESTION INTENT MODEL
# ============================================================

class OfficialIntent(BaseModel):

    action: Literal[
        "count",
        "list",
        "search",
        "get_by_id",
        "get_by_slot",
        "clarify",
        "unsupported"
    ]

    department_code: str | None = None

    department_slot: int | None = Field(
        default=None,
        ge=1
    )

    grievance_id: str | None = None

    search_query: str | None = None

    clarification: str | None = None


# ============================================================
# 2. DEPARTMENT ALIASES
# ============================================================

DEPARTMENT_ALIASES = {

    "KSRTC": "TRANSPORT",
    "TRANSPORT": "TRANSPORT",
    "TRANSPORT DEPARTMENT": "TRANSPORT",

    "WATER": "KWA",
    "WATER AUTHORITY": "KWA",
    "KERALA WATER AUTHORITY": "KWA",

    "ELECTRICITY": "KSEB",
    "ELECTRICITY BOARD": "KSEB",

    "PUBLIC WORKS": "PWD",
    "PUBLIC WORKS DEPARTMENT": "PWD",

    "LOCAL BODY": "LSGD",
    "LOCAL SELF GOVERNMENT": "LSGD",

    "REVENUE DEPARTMENT": "REVENUE",

    "POLICE DEPARTMENT": "POLICE",

    "HEALTH DEPARTMENT": "HEALTH",

    "EDUCATION DEPARTMENT": "EDUCATION",

    "CIVIL SUPPLIES DEPARTMENT": "CIVIL_SUPPLIES",

    "SOCIAL JUSTICE DEPARTMENT": "SOCIAL_JUSTICE",
}


def normalize_department(value: str | None) -> str | None:

    if not value:
        return None

    code = re.sub(
        r"\s+",
        " ",
        value.strip().upper()
    )

    if code in database.DEPARTMENTS:
        return code

    return DEPARTMENT_ALIASES.get(code)



# ============================================================
# 3.1 HISTORY CONTEXT AND DETERMINISTIC EXTRACTION HELPERS
# ============================================================

HISTORY_RECORD_MARKER = "Retrieved grievance records:"

MALAYALAM_SLOT_ORDINALS = (
    ("ഒന്നാമത്തെ", 1), ("ഒന്നാം", 1),
    ("രണ്ടാമത്തെ", 2), ("രണ്ടാം", 2),
    ("മൂന്നാമത്തെ", 3), ("മൂന്നാം", 3),
    ("നാലാമത്തെ", 4), ("നാലാം", 4),
    ("അഞ്ചാമത്തെ", 5), ("അഞ്ചാം", 5),
    ("ആറാമത്തെ", 6), ("ആറാം", 6),
    ("ഏഴാമത്തെ", 7), ("ഏഴാം", 7),
    ("എട്ടാമത്തെ", 8), ("എട്ടാം", 8),
    ("ഒമ്പതാമത്തെ", 9), ("ഒമ്പതാം", 9),
    ("പത്താമത്തെ", 10), ("പത്താം", 10),
)

ENGLISH_ORDINALS = {
    "first": 1, "1st": 1,
    "second": 2, "2nd": 2,
    "third": 3, "3rd": 3,
    "fourth": 4, "4th": 4,
    "fifth": 5, "5th": 5,
    "sixth": 6, "6th": 6,
    "seventh": 7, "7th": 7,
    "eighth": 8, "8th": 8,
    "ninth": 9, "9th": 9,
    "tenth": 10, "10th": 10,
}

MANGLISH_ORDINALS = {
    "onnam": 1,
    "onnu": 1,
    "randam": 2,
    "randaam": 2,
    "randamathe": 2,
    "moonam": 3,
    "moonnam": 3,
    "moonnamathe": 3,
    "nalam": 4,
    "naalam": 4,
    "nalamathe": 4,
    "ancham": 5,
    "anjaam": 5,
    "aaram": 6,
    "aaramathe": 6,
}


def _clean_history_record(record: object) -> dict | None:
    """Keep only trusted fields needed to resolve previous results."""
    if not isinstance(record, dict):
        return None

    grievance_id = record.get("grievance_id")
    department_code = record.get("department_code")
    department_slot = record.get("department_slot")

    if not grievance_id and not (department_code and department_slot):
        return None

    return {
        "grievance_id": str(grievance_id) if grievance_id else None,
        "department_code": str(department_code) if department_code else None,
        "department_slot": department_slot,
        "citizen_name": str(record.get("citizen_name") or "").strip(),
        "status": record.get("status"),
    }


def _extract_history_records(
    history: list[dict] | None,
) -> tuple[list[list[dict]], list[dict]]:
    """Read record lists embedded by OfficialPage in prior assistant messages."""
    record_lists: list[list[dict]] = []
    all_records: list[dict] = []
    seen_ids: set[str] = set()

    for message in history or []:
        if message.get("role") != "assistant":
            continue

        content = str(message.get("content") or "")
        if HISTORY_RECORD_MARKER not in content:
            continue

        payload = content.split(HISTORY_RECORD_MARKER, 1)[1].strip()
        if not payload:
            continue

        try:
            parsed, _end = json.JSONDecoder().raw_decode(payload)
        except (json.JSONDecodeError, TypeError, ValueError):
            # A truncated history message is ignored rather than guessed from.
            continue

        if isinstance(parsed, list):
            cleaned_list = [
                cleaned
                for item in parsed
                if (cleaned := _clean_history_record(item)) is not None
            ]
            record_lists.append(cleaned_list)
            candidates = cleaned_list
        elif isinstance(parsed, dict):
            cleaned = _clean_history_record(parsed)
            candidates = [cleaned] if cleaned else []
        else:
            candidates = []

        for record in candidates:
            record_id = record.get("grievance_id")
            dedupe_key = (
                record_id
                or f"{record.get('department_code')}:{record.get('department_slot')}:{record.get('citizen_name')}"
            )
            if dedupe_key not in seen_ids:
                seen_ids.add(dedupe_key)
                all_records.append(record)

    return record_lists, all_records


def _extract_explicit_slot_number(question: str) -> int | None:
    """Extract a slot explicitly stated in English, Manglish or Malayalam."""
    text = question.casefold()

    numeric_patterns = (
        r"(?<!\d)(\d+)(?:st|nd|rd|th)?\s*(?:slot|സ്ലോട്ട്)",
        r"(?:slot|സ്ലോട്ട്)\s*(?:number\s*|no\.?\s*|നമ്പർ\s*)?(\d+)",
    )
    for pattern in numeric_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            number = int(match.group(1))
            if number >= 1:
                return number

    word_ordinals = {
        **ENGLISH_ORDINALS,
        **MANGLISH_ORDINALS,
    }
    for word, number in sorted(word_ordinals.items(), key=lambda item: -len(item[0])):
        if re.search(rf"(?<![a-z]){re.escape(word)}\s+slot\b", text):
            return number

    if "സ്ലോട്ട" in text:
        for word, number in MALAYALAM_SLOT_ORDINALS:
            if word in text:
                return number

    return None


def _extract_contextual_ordinal(question: str) -> int | None:
    """Resolve phrases such as 'second one' against a previous result list."""
    text = question.casefold()

    # An explicit department slot is handled by slot extraction, not list order.
    if "slot" in text or "സ്ലോട്ട" in text:
        return None

    contextual_targets = (
        "one", "complaint", "grievance", "record", "result", "case",
    )

    for word, number in sorted(ENGLISH_ORDINALS.items(), key=lambda item: -len(item[0])):
        for target in contextual_targets:
            pattern = rf"(?<![a-z0-9]){re.escape(word)}\s+{target}\w*"
            if re.search(pattern, text):
                return number

    # Common Malayalam ordinal references to an item in the previous list.
    malayalam_context_ordinals = (
        ("ഒന്നാമത്തെ", 1), ("ഒന്നാം", 1),
        ("രണ്ടാമത്തെ", 2), ("രണ്ടാം", 2),
        ("മൂന്നാമത്തെ", 3), ("മൂന്നാം", 3),
        ("നാലാമത്തെ", 4), ("നാലാം", 4),
        ("അഞ്ചാമത്തെ", 5), ("അഞ്ചാം", 5),
    )
    if any(term in text for term in ("പരാതി", "ഗ്രീവൻസ്", "റെക്കോർഡ്", "ഒന്ന്", "ഒന്നാമത്തെ", "രണ്ടാം", "മൂന്നാം")):
        for word, number in malayalam_context_ordinals:
            if word in text:
                return number

    return None


def _name_is_explicitly_mentioned(question: str, name: str) -> bool:
    """Match a known citizen name as a whole name, including 'Anitha-yude'."""
    name = (name or "").strip()
    if not name:
        return False

    escaped_name = r"\s+".join(re.escape(part) for part in name.split())
    pattern = rf"(?<!\w){escaped_name}(?!\w)"
    return re.search(pattern, question, flags=re.IGNORECASE) is not None


def _apply_history_context(
    question: str,
    history: list[dict] | None,
    intent: OfficialIntent,
) -> OfficialIntent:
    """Resolve citizen-name and numbered-list follow-ups from actual prior records."""
    record_lists, all_records = _extract_history_records(history)
    if not all_records:
        return intent

    # Never override an exact grievance ID explicitly supplied by the user.
    if re.search(r"\bGRV-[A-Z0-9_-]+\b", question, flags=re.IGNORECASE):
        return intent

    # Resolve a citizen name against the actual records in prior results.
    # If exactly one previous record matches and the official asks for its
    # details, retrieve that exact record by ID. If the name is ambiguous,
    # keep a normal name search rather than guessing which grievance is meant.
    matching_records = [
        record
        for record in all_records
        if record.get("citizen_name")
        and _name_is_explicitly_mentioned(question, record["citizen_name"])
    ]

    if matching_records:
        unique_names = {record["citizen_name"] for record in matching_records}
        detail_request = bool(
            re.search(
                r"\b(full|complete|details?|information|info)\b|"
                r"വിശദാംശ|വിവരങ്ങൾ|വിവരം",
                question,
                flags=re.IGNORECASE,
            )
        )

        if len(unique_names) == 1 and len(matching_records) == 1 and detail_request:
            matched_record = matching_records[0]
            grievance_id = matched_record.get("grievance_id")

            if grievance_id:
                intent.action = "get_by_id"
                intent.department_code = None
                intent.department_slot = None
                intent.grievance_id = grievance_id
                intent.search_query = None
                intent.clarification = None
                return intent

        # A general name search, or a name attached to multiple records,
        # remains a search operation. Do not guess an individual record.
        if len(unique_names) == 1:
            matched_name = next(iter(unique_names))
            intent.action = "search"
            intent.department_code = None
            intent.department_slot = None
            intent.grievance_id = None
            intent.search_query = matched_name
            intent.clarification = None
            return intent

    # Resolve 'second one', 'third complaint', etc. using the latest actual result list.
    ordinal = _extract_contextual_ordinal(question)
    if ordinal is None or not record_lists:
        return intent

    latest_records = record_lists[-1]
    index = ordinal - 1

    if index < 0 or index >= len(latest_records):
        intent.action = "clarify"
        intent.department_code = None
        intent.department_slot = None
        intent.grievance_id = None
        intent.search_query = None
        intent.clarification = (
            f"The previous result list does not contain item {ordinal}. "
            "Please request a result number that was shown."
        )
        return intent

    selected = latest_records[index]
    intent.grievance_id = selected.get("grievance_id")
    intent.department_code = selected.get("department_code")
    intent.department_slot = selected.get("department_slot")
    intent.search_query = None
    intent.clarification = None

    if intent.grievance_id:
        # A unique ID avoids collisions when the list spans departments.
        intent.action = "get_by_id"
        intent.department_code = None
        intent.department_slot = None
    elif intent.department_code and intent.department_slot:
        intent.action = "get_by_slot"
    else:
        intent.action = "clarify"
        intent.clarification = "I could not identify that item in the previous results. Please provide its grievance ID."

    return intent


# ============================================================
# 3. UNDERSTAND THE OFFICIAL'S QUESTION
# ============================================================

def understand_question(
    question: str,
    history: list[dict] | None = None
) -> OfficialIntent:
    """
    Convert a natural-language question into a validated intent.

    History allows follow-up questions such as:
    "Show the third slot" after asking for KSEB cases.
    """

    recent_history = []

    for message in (history or [])[-10:]:

        role = message.get("role", "")

        content = str(
            message.get("content", "")
        ).strip()

        if role in ("user", "assistant") and content:

            recent_history.append(
                f"{role.upper()}: {content[:5000]}"
            )

    history_text = "\n".join(recent_history)

    departments = ", ".join(
        database.DEPARTMENTS
    )

    prompt = f"""
You are the intent-understanding component of a government
grievance database assistant.

Your task is ONLY to identify what database operation
the official is requesting.

AVAILABLE DEPARTMENT CODES:
{departments}

IMPORTANT DEPARTMENT ALIAS:
KSRTC belongs to the TRANSPORT department.

LANGUAGE UNDERSTANDING:

The official may communicate in:

1. English.
2. Malayalam script.
3. Manglish — Malayalam written using English letters.
4. Mixed Malayalam and English.

Understand informal Malayalam transliteration,
spelling variations and code-mixed expressions.

Examples:

- "ethra complaints register cheythittundu?"
  means count all registered grievances.

- "KSEB yil ethra complaints undu?"
  means count KSEB grievances.

- "KSEB il register cheytha complaints kanikku"
  means list KSEB grievances.

- "aa complaint inte details parayu"
  means retrieve the previously identified grievance.

- "third slot inte details venam"
  means retrieve the third result or slot using
  the available conversation context.

Do not invent missing department names, IDs or slots.
If context is insufficient, ask for clarification.

Always return the same OfficialIntent JSON structure.

ADDITIONAL MANGLISH EXAMPLES:

COUNT:
- "ethra complaints undu?"
- "total complaints ethra aanu?"
- "ithuvare ethra grievances register aayi?"
- "complaint count parayamo?"

LIST:
- "KSEB complaints ellam kanikku"
- "KWA yil register cheytha cases list cheyyu"
- "KSRTC complaints details list cheythu tharu"

SEARCH:
- "Ramesh inte complaint search cheyyu"
- "GRV-KSEB-0001 kandupidikku"
- "Anitha enna aalude complaint undo?"

RETRIEVE:
- "GRV-KWA-0002 inte full details parayu"
- "KSEB le first complaint eduthu kanikku"
- "aa complaint inte details venam"
- "third one inte details parayu"
- "കെഎസ്ഇബിയിലെ രണ്ടാം സ്ലോട്ടിന്റെ വിശദാംശങ്ങൾ കാണിക്കുക" means KSEB slot 2.
- "കെഎസ്ഇബിയിലെ മൂന്നാം സ്ലോട്ടിന്റെ വിവരങ്ങൾ വേണം" means KSEB slot 3.

FOLLOW-UP QUESTIONS:
- "athinte status entha?"
- "aa complaint eppozha register cheythathu?"
- "second complaint aanu njan uddeshichathu"

IMPORTANT:
- Understand spelling variations in Romanized Malayalam.
- Understand English words mixed with Malayalam.
- Use conversation history to resolve references.
- Preserve exact grievance IDs.
- Never invent a citizen name, department or slot.
- Ask for clarification when the requested record is ambiguous.

AVAILABLE OPERATIONS:

count:
The official wants the total number of registered grievances.
May include one particular department.

list:
The official wants a list of registered grievances.
May include one particular department.

search:
The official wants to find grievances using a person's name
or a grievance registration ID.

get_by_id:
The official wants the complete details of one grievance
using its unique registration ID.

get_by_slot:
The official wants the complete details of a grievance
using a department and its slot number.

clarify:
The question is missing information necessary to identify
the requested record or operation.

unsupported:
The question is unrelated to grievance database retrieval.

RULES:

1. Never invent a department code, name, registration ID or slot.
2. Use only the department codes provided above.
3. Map KSRTC to TRANSPORT.
4. If the official asks for all grievances without specifying
   a department, use a null department_code.
5. If the official asks for a specific slot without enough
   department context, select clarify.
6. Use previous conversation messages to understand follow-up
   questions, including references such as "that department"
   or "the third slot".
7. When the official refers to "the first one", "second one",
   "third one", or another numbered result, inspect the
   retrieved grievance records in the conversation history.

8. Interpret numbered results using their displayed order,
   starting from 1.

9. If the requested result has a grievance_id, return:
   action = "get_by_id"
   grievance_id = the exact ID from the previous results.

10. If the official asks for a department slot, retrieve
    the department code from the preceding conversation
    when it is unambiguous.

11. Never invent an ID, department or slot number.

12. If the requested record cannot be identified from
    conversation history, ask for clarification.

RECENT CONVERSATION:
{history_text}

CURRENT OFFICIAL QUESTION:
{question}
"""

    # ========================================================
    # HOSTED GEMMA 4 — OFFICIAL INTENT UNDERSTANDING
    # ========================================================

    try:
        # Reuse the same Google GenAI client and hosted model as rag.py.
        # This avoids requiring a local Ollama server on Render.
        from rag import gemma_client, CHAT_MODEL
        from google.genai import types

        response = gemma_client.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=OfficialIntent,
                temperature=0,
                max_output_tokens=512
            )
        )

        content = (response.text or "").strip()

        if not content:
            raise RuntimeError(
                "Hosted Gemma returned an empty intent response."
            )

        intent = OfficialIntent.model_validate_json(content)

    except Exception as error:
        raise RuntimeError(
            f"Hosted Official AI model failed: {error}"
        ) from error

    # Fill an explicitly stated slot number deterministically. This supports
    # Arabic digits, English ordinals, Manglish and Malayalam-script ordinals.
    explicit_slot = _extract_explicit_slot_number(question)
    if intent.action == "get_by_slot" and explicit_slot is not None:
        intent.department_slot = explicit_slot

    # Resolve references to previous results using the actual records
    # embedded in conversation history, not model-generated guesses.
    intent = _apply_history_context(question, history, intent)

    # --------------------------------------------------------
    # Validate the requested department.
    # Never silently convert an unknown department into
    # an all-departments query.
    # --------------------------------------------------------

    raw_department = intent.department_code

    normalized_department = normalize_department(
        raw_department
    )

    all_department_labels = {
        "ALL",
        "ALL DEPARTMENTS",
        "ALL DEPARTMENT",
        "ACROSS ALL DEPARTMENTS",
    }

    if raw_department:

        cleaned_department = raw_department.strip().upper()

        if cleaned_department in all_department_labels:
            # Explicit request for all departments.
            intent.department_code = None

        elif normalized_department is None:
            # Unknown department: ask for clarification.
            intent.action = "clarify"
            intent.department_code = None
            intent.clarification = (
                f"I could not identify the department "
                f"'{raw_department}'. Please specify a valid "
                "department such as KSEB, KWA, PWD or KSRTC."
            )

        else:
            intent.department_code = normalized_department

    return intent


# ============================================================
# 4. FORMAT A DATABASE RECORD FOR THE OFFICIAL PORTAL
# ============================================================

def prepare_record(record: dict) -> dict:

    record = dict(record)

    # Do not return the server's internal filesystem path.
    record.pop("document_path", None)

    grievance_id = record.get("grievance_id")

    if grievance_id:

        record["document_url"] = (
            f"/official/grievances/id/{grievance_id}/document"
        )

    return record


# ============================================================
# 5. PROCESS THE OFFICIAL'S QUESTION
# ============================================================

def answer_official_question(
    question: str,
    history: list[dict] | None = None
) -> dict:
    """
    Understand the official's question and retrieve
    the corresponding records from the SQLite database.
    """

    question = (question or "").strip()

    if not question:

        raise ValueError(
            "Please enter a question."
        )

    intent = understand_question(
        question,
        history
    )

    action = intent.action

    department = intent.department_code

    # --------------------------------------------------------
    # A. COUNT REGISTERED GRIEVANCES
    # --------------------------------------------------------

    if action == "count":

        counts = database.get_grievance_counts()

        if department:

            department_data = next(
                (
                    item
                    for item in counts["departments"]
                    if item["department_code"] == department
                ),
                None
            )

            if department_data is None:
                raise RuntimeError(
                    "Department count was not available."
                )

            total = department_data["total"]

            return {
                "action": "count",
                "reply": (
                    f"{total} grievances are registered "
                    f"under {department}."
                ),
                "data": department_data
            }

        return {
            "action": "count",
            "reply": (
                f"A total of {counts['total']} grievances "
                "are registered across all departments."
            ),
            "data": counts
        }

    # --------------------------------------------------------
    # B. LIST ALL OR DEPARTMENT-WISE GRIEVANCES
    # --------------------------------------------------------

    if action == "list":

        records = database.list_grievances(
            department_code=department,
            limit=100,
            offset=0
        )

        records = [
            prepare_record(record)
            for record in records
        ]

        department_text = (
            f" under {department}"
            if department
            else " across all departments"
        )

        return {
            "action": "list",
            "reply": (
                f"Found {len(records)} grievance records"
                f"{department_text}. Showing up to 100 records."
            ),
            "count": len(records),
            "data": records
        }

    # --------------------------------------------------------
    # C. SEARCH BY CITIZEN NAME OR GRIEVANCE ID
    # --------------------------------------------------------

    if action == "search":

        if not intent.search_query:

            return {
                "action": "clarify",
                "reply": (
                    "Please provide a citizen name "
                    "or grievance registration ID."
                ),
                "data": None
            }

        records = database.search_grievances(
            query=intent.search_query,
            department_code=department,
            limit=50
        )

        records = [
            prepare_record(record)
            for record in records
        ]

        return {
            "action": "search",
            "reply": (
                f"Found {len(records)} matching grievance records."
            ),
            "count": len(records),
            "data": records
        }

    # --------------------------------------------------------
    # D. RETRIEVE USING UNIQUE GRIEVANCE ID
    # --------------------------------------------------------

    if action == "get_by_id":

        if not intent.grievance_id:

            return {
                "action": "clarify",
                "reply": (
                    "Please provide the grievance registration ID."
                ),
                "data": None
            }

        record = database.get_grievance_by_id(
            intent.grievance_id
        )

        if record is None:

            return {
                "action": "get_by_id",
                "reply": "No grievance was found with that ID.",
                "data": None
            }

        return {
            "action": "get_by_id",
            "reply": (
                f"Retrieved grievance {intent.grievance_id}."
            ),
            "data": prepare_record(record)
        }

    # --------------------------------------------------------
    # E. RETRIEVE USING DEPARTMENT SLOT
    # --------------------------------------------------------

    if action == "get_by_slot":

        if not department:

            return {
                "action": "clarify",
                "reply": (
                    "Please specify the department so I can "
                    "identify the correct slot."
                ),
                "data": None
            }

        if not intent.department_slot:

            return {
                "action": "clarify",
                "reply": "Please specify the department slot number.",
                "data": None
            }

        record = database.get_grievance_by_department_slot(
            department,
            intent.department_slot
        )

        if record is None:

            return {
                "action": "get_by_slot",
                "reply": (
                    f"No grievance was found in {department} "
                    f"slot {intent.department_slot}."
                ),
                "data": None
            }

        return {
            "action": "get_by_slot",
            "reply": (
                f"Retrieved {department} grievance "
                f"slot {intent.department_slot}."
            ),
            "data": prepare_record(record)
        }

    # --------------------------------------------------------
    # F. CLARIFICATION
    # --------------------------------------------------------

    if action == "clarify":

        return {
            "action": "clarify",
            "reply": (
                intent.clarification
                or "Please provide more information about the grievance."
            ),
            "data": None
        }

    # --------------------------------------------------------
    # G. UNSUPPORTED QUESTION
    # --------------------------------------------------------

    return {
        "action": "unsupported",
        "reply": (
            "I can help you count, list, search and retrieve "
            "registered grievances. Please ask a question "
            "related to grievance records."
        ),
        "data": None
    }