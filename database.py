
from pathlib import Path
import sqlite3
import shutil
from datetime import datetime

# ============================================================
# 1. DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "grievances.db"

# Keep grievance files separate from the existing RAG documents.
GRIEVANCE_STORAGE = BASE_DIR / "grievance_storage"
DEPARTMENT_STORAGE = GRIEVANCE_STORAGE / "departments"


# ============================================================
# 2. DEPARTMENT DEFINITIONS
# ============================================================

DEPARTMENTS = [
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
    "OTHER",
]


# ============================================================
# 3. DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a connection to the grievance database.
    """

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# 4. INITIALIZE DATABASE AND TABLES
# ============================================================

def init_db():
    """
    Create the grievance database, required tables
    and department-wise document storage folders.
    """

    # Create department folders.
    for department in DEPARTMENTS:
        folder = DEPARTMENT_STORAGE / department

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

    connection = get_connection()

    try:
        connection.execute(
            "PRAGMA journal_mode = WAL"
        )

        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS grievances (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                grievance_id TEXT NOT NULL UNIQUE,

                department_code TEXT NOT NULL,

                department_slot INTEGER NOT NULL,

                citizen_name TEXT,

                original_filename TEXT NOT NULL,

                document_path TEXT NOT NULL,

                summary TEXT NOT NULL,

                description TEXT NOT NULL,

                department_reason TEXT,

                original_language TEXT DEFAULT 'unknown',

                response_language TEXT DEFAULT 'en',

                status TEXT NOT NULL DEFAULT 'REGISTERED',

                registered_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (
                    department_code,
                    department_slot
                ),

                CHECK (department_slot > 0)

            );


            CREATE INDEX IF NOT EXISTS
                idx_grievances_department
            ON grievances(department_code);


            CREATE INDEX IF NOT EXISTS
                idx_grievances_citizen
            ON grievances(citizen_name);


            CREATE INDEX IF NOT EXISTS
                idx_grievances_status
            ON grievances(status);


            CREATE INDEX IF NOT EXISTS
                idx_grievances_registered_at
            ON grievances(registered_at);

            """
        )

        connection.commit()

    finally:
        connection.close()


# ============================================================
# 5. INITIALIZE DATABASE WHEN RUN DIRECTLY
# ============================================================



# ============================================================
# 5. OFFICIAL GRIEVANCE RETRIEVAL
# ============================================================

def get_grievance_counts() -> dict:
    """
    Return the total number of registered grievances
    and department-wise counts.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT department_code, COUNT(*) AS total
            FROM grievances
            GROUP BY department_code
            """
        ).fetchall()

        counts = {
            department: 0
            for department in DEPARTMENTS
        }

        for row in rows:
            counts[row["department_code"]] = row["total"]

        return {
            "total": sum(counts.values()),
            "departments": [
                {
                    "department_code": code,
                    "total": total
                }
                for code, total in counts.items()
            ]
        }

    finally:
        connection.close()


# ============================================================
# 6. LIST REGISTERED GRIEVANCES
# ============================================================

def list_grievances(
    department_code: str | None = None,
    limit: int = 100,
    offset: int = 0
) -> list[dict]:
    """
    Retrieve grievance records.

    Optionally filter by department.
    Supports pagination.
    """

    if limit < 1 or limit > 500:
        raise ValueError("Limit must be between 1 and 500.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    connection = get_connection()

    try:
        if department_code:
            department_code = department_code.strip().upper()

            if department_code not in DEPARTMENTS:
                raise ValueError("Invalid department code.")

            rows = connection.execute(
                """
                SELECT
                    grievance_id,
                    department_code,
                    department_slot,
                    citizen_name,
                    summary,
                    registered_at,
                    status
                FROM grievances
                WHERE department_code = ?
                ORDER BY department_slot ASC
                LIMIT ? OFFSET ?
                """,
                (department_code, limit, offset)
            ).fetchall()

        else:
            rows = connection.execute(
                """
                SELECT
                    grievance_id,
                    department_code,
                    department_slot,
                    citizen_name,
                    summary,
                    registered_at,
                    status
                FROM grievances
                ORDER BY registered_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


# ============================================================
# 7. RETRIEVE GRIEVANCE BY UNIQUE ID
# ============================================================

def get_grievance_by_id(
    grievance_id: str
) -> dict | None:
    """
    Retrieve the complete details of one grievance
    using its unique registration ID.
    """

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM grievances
            WHERE grievance_id = ?
            """,
            (grievance_id.strip(),)
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


# ============================================================
# 8. RETRIEVE GRIEVANCE BY DEPARTMENT SLOT
# ============================================================

def get_grievance_by_department_slot(
    department_code: str,
    department_slot: int
) -> dict | None:
    """
    Retrieve an individual grievance using
    its department and sequential slot number.
    """

    department_code = department_code.strip().upper()

    if department_code not in DEPARTMENTS:
        raise ValueError("Invalid department code.")

    if department_slot < 1:
        raise ValueError("Department slot must be positive.")

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM grievances
            WHERE department_code = ?
              AND department_slot = ?
            """,
            (department_code, department_slot)
        ).fetchone()

        return dict(row) if row else None

    finally:
        connection.close()


# ============================================================
# 9. SEARCH GRIEVANCES BY NAME OR REGISTRATION ID
# ============================================================

def search_grievances(
    query: str,
    department_code: str | None = None,
    limit: int = 50
) -> list[dict]:
    """
    Search grievance records by citizen name
    or unique registration ID.

    Optionally restrict the search to a department.
    """

    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty.")

    if limit < 1 or limit > 500:
        raise ValueError("Limit must be between 1 and 500.")

    search_value = f"%{query.lower()}%"

    connection = get_connection()

    try:
        if department_code:
            department_code = department_code.strip().upper()

            if department_code not in DEPARTMENTS:
                raise ValueError("Invalid department code.")

            rows = connection.execute(
                """
                SELECT
                    grievance_id,
                    department_code,
                    department_slot,
                    citizen_name,
                    summary,
                    registered_at,
                    status
                FROM grievances
                WHERE department_code = ?
                  AND (
                      LOWER(COALESCE(citizen_name, '')) LIKE ?
                      OR LOWER(grievance_id) LIKE ?
                  )
                ORDER BY department_slot ASC
                LIMIT ?
                """,
                (
                    department_code,
                    search_value,
                    search_value,
                    limit
                )
            ).fetchall()

        else:
            rows = connection.execute(
                """
                SELECT
                    grievance_id,
                    department_code,
                    department_slot,
                    citizen_name,
                    summary,
                    registered_at,
                    status
                FROM grievances
                WHERE
                    LOWER(COALESCE(citizen_name, '')) LIKE ?
                    OR LOWER(grievance_id) LIKE ?
                ORDER BY registered_at DESC
                LIMIT ?
                """,
                (search_value, search_value, limit)
            ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


# ============================================================
# 5. REGISTER A NEW GRIEVANCE
# ============================================================

def register_grievance(
    department_code: str,
    original_filename: str,
    document_bytes: bytes,
    summary: str,
    description: str,
    department_reason: str,
    citizen_name: str | None = None,
    original_language: str = "unknown",
    response_language: str = "en",
) -> dict:
    """
    Register a grievance, assign its department slot,
    save the original document and insert its details
    into the central SQLite database.
    """

    # Validate department.
    if department_code not in DEPARTMENTS:
        raise ValueError("Invalid department code.")

    # Validate uploaded document.
    if not document_bytes:
        raise ValueError("The uploaded document is empty.")

    # Keep only the extension; never use the supplied filename
    # as a filesystem path.
    from pathlib import Path

    extension = Path(original_filename).suffix.lower()

    if extension not in (".jpg", ".jpeg", ".png", ".webp", ".pdf"):
        raise ValueError("Unsupported document format.")

    connection = get_connection()

    record_folder = None

    try:
        # Prevent two simultaneous registrations from receiving
        # the same department slot.
        connection.execute("BEGIN IMMEDIATE")

        row = connection.execute(
            """
            SELECT COALESCE(MAX(department_slot), 0) + 1
            AS next_slot
            FROM grievances
            WHERE department_code = ?
            """,
            (department_code,)
        ).fetchone()

        department_slot = row["next_slot"]

        grievance_id = (
            f"GRV-{department_code}-{department_slot:04d}"
        )

        # Create a separate folder for this grievance.
        record_folder = (
            DEPARTMENT_STORAGE
            / department_code
            / grievance_id
        )

        record_folder.mkdir(
            parents=True,
            exist_ok=False
        )

        document_file = record_folder / f"original{extension}"

        # Save the original document.
        with open(document_file, "xb") as file:
            file.write(document_bytes)

        relative_document_path = (
            document_file.relative_to(BASE_DIR).as_posix()
        )

        # Store the extracted information.
        connection.execute(
            """
            INSERT INTO grievances (
                grievance_id,
                department_code,
                department_slot,
                citizen_name,
                original_filename,
                document_path,
                summary,
                description,
                department_reason,
                original_language,
                response_language,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                grievance_id,
                department_code,
                department_slot,
                citizen_name,
                Path(original_filename).name,
                relative_document_path,
                summary,
                description,
                department_reason,
                original_language,
                response_language,
                "REGISTERED",
            )
        )

        connection.commit()

        return {
            "grievance_id": grievance_id,
            "department_code": department_code,
            "department_slot": department_slot,
            "citizen_name": citizen_name,
            "document_path": relative_document_path,
            "status": "REGISTERED",
        }

    except Exception:
        connection.rollback()

        # Remove the saved file if database registration fails.
        if record_folder and record_folder.exists():
            for item in record_folder.iterdir():
                if item.is_file():
                    item.unlink()

            record_folder.rmdir()

        raise

    finally:
        connection.close()


# ============================================================
# 10. UPDATE GRIEVANCE STATUS
# ============================================================

ALLOWED_STATUSES = {
    "REGISTERED",
    "UNDER_REVIEW",
    "IN_PROGRESS",
    "RESOLVED",
    "REJECTED",
    "CLOSED",
}


def update_grievance_status(
    grievance_id: str,
    new_status: str
) -> dict | None:
    """
    Update the status of an existing grievance.

    Returns the updated record, or None if the
    grievance ID does not exist.
    """

    grievance_id = grievance_id.strip()
    new_status = new_status.strip().upper()

    if not grievance_id:
        raise ValueError("Grievance ID cannot be empty.")

    if new_status not in ALLOWED_STATUSES:
        raise ValueError(
            "Invalid status. Allowed values: "
            + ", ".join(sorted(ALLOWED_STATUSES))
        )

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")

        cursor = connection.execute(
            """
            UPDATE grievances
            SET
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE grievance_id = ?
            """,
            (new_status, grievance_id)
        )

        if cursor.rowcount == 0:
            connection.rollback()
            return None

        row = connection.execute(
            """
            SELECT *
            FROM grievances
            WHERE grievance_id = ?
            """,
            (grievance_id,)
        ).fetchone()

        connection.commit()

        return dict(row)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ============================================================
# 11. DATABASE MANAGEMENT OPERATIONS
# ============================================================

def list_management_grievances(
    department_code: str | None = None,
    status: str | None = None,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 500,
    offset: int = 0
) -> list[dict]:
    """List grievance records with management filters."""

    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500.")

    if offset < 0:
        raise ValueError("Offset cannot be negative.")

    conditions = []
    parameters = []

    if department_code:
        department_code = department_code.strip().upper()

        if department_code not in DEPARTMENTS:
            raise ValueError("Invalid department code.")

        conditions.append("department_code = ?")
        parameters.append(department_code)

    if status:
        status = status.strip().upper()

        if status not in ALLOWED_STATUSES:
            raise ValueError("Invalid grievance status.")

        conditions.append("status = ?")
        parameters.append(status)

    if search and search.strip():
        value = f"%{search.strip().lower()}%"
        conditions.append("""
            (
                LOWER(grievance_id) LIKE ?
                OR LOWER(COALESCE(citizen_name, '')) LIKE ?
                OR LOWER(summary) LIKE ?
            )
        """)
        parameters.extend([value, value, value])

    for value in (date_from, date_to):
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError as error:
                raise ValueError(
                    "Dates must use YYYY-MM-DD format."
                ) from error

    if date_from:
        conditions.append("date(registered_at) >= date(?)")
        parameters.append(date_from)

    if date_to:
        conditions.append("date(registered_at) <= date(?)")
        parameters.append(date_to)

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    connection = get_connection()

    try:
        rows = connection.execute(
            f"""
            SELECT
                grievance_id,
                department_code,
                department_slot,
                citizen_name,
                original_filename,
                summary,
                description,
                department_reason,
                registered_at,
                updated_at,
                status
            FROM grievances
            {where_clause}
            ORDER BY registered_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*parameters, limit, offset)
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def update_grievance_record(
    grievance_id: str,
    citizen_name: str | None,
    summary: str,
    description: str,
    department_reason: str | None,
    status: str
) -> dict | None:
    """Edit the permitted fields of an existing grievance."""

    grievance_id = grievance_id.strip()
    status = status.strip().upper()

    if status not in ALLOWED_STATUSES:
        raise ValueError("Invalid grievance status.")

    if not summary.strip():
        raise ValueError("Summary cannot be empty.")

    if not description.strip():
        raise ValueError("Description cannot be empty.")

    citizen_name = (citizen_name or "").strip() or None
    department_reason = (
        (department_reason or "").strip() or None
    )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE grievances
            SET
                citizen_name = ?,
                summary = ?,
                description = ?,
                department_reason = ?,
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE grievance_id = ?
            """,
            (
                citizen_name,
                summary.strip(),
                description.strip(),
                department_reason,
                status,
                grievance_id
            )
        )

        if cursor.rowcount == 0:
            connection.rollback()
            return None

        row = connection.execute(
            """
            SELECT *
            FROM grievances
            WHERE grievance_id = ?
            """,
            (grievance_id,)
        ).fetchone()

        connection.commit()
        return dict(row)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def _get_safe_grievance_folder(
    document_path: str | None
) -> Path | None:
    """
    Resolve an original document path and verify that it
    belongs to the expected department/grievance folder.
    """

    if not document_path:
        return None

    candidate = Path(document_path)

    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate

    candidate = candidate.resolve()
    storage_root = DEPARTMENT_STORAGE.resolve()

    try:
        relative = candidate.relative_to(storage_root)
    except ValueError:
        return None

    if len(relative.parts) != 3:
        return None

    department, folder_name, filename = relative.parts

    if department not in DEPARTMENTS:
        return None

    if not folder_name.startswith(f"GRV-{department}-"):
        return None

    if not filename.startswith("original."):
        return None

    folder = (storage_root / department / folder_name).resolve()

    if folder.parent != (
        storage_root / department
    ).resolve():
        return None

    return folder


def _delete_matching_records(
    where_clause: str,
    parameters: tuple = (),
    reset_sequence: bool = False
) -> dict:
    """Delete matching database rows and their document folders."""

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")

        rows = connection.execute(
            f"""
            SELECT grievance_id, document_path
            FROM grievances
            {where_clause}
            """,
            parameters
        ).fetchall()

        records = [dict(row) for row in rows]
        grievance_ids = [
            row["grievance_id"] for row in records
        ]

        if grievance_ids:
            placeholders = ",".join(
                "?" for _ in grievance_ids
            )

            connection.execute(
                f"""
                DELETE FROM grievances
                WHERE grievance_id IN ({placeholders})
                """,
                grievance_ids
            )

        if reset_sequence:
            connection.execute(
                """
                DELETE FROM sqlite_sequence
                WHERE name = 'grievances'
                """
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    # Remove only the original-document folder belonging
    # to each deleted grievance.
    documents_removed = 0
    cleanup_errors = []

    for record in records:
        folder = _get_safe_grievance_folder(
            record["document_path"]
        )

        if folder is None or not folder.exists():
            continue

        try:
            shutil.rmtree(folder)
            documents_removed += 1
        except OSError as error:
            cleanup_errors.append(
                f"{record['grievance_id']}: {error}"
            )

    return {
        "deleted_count": len(grievance_ids),
        "deleted_grievance_ids": grievance_ids,
        "document_folders_removed": documents_removed,
        "cleanup_errors": cleanup_errors
    }


def delete_grievances_by_ids(
    grievance_ids: list[str]
) -> dict:
    """Delete selected grievance records."""

    ids = list(dict.fromkeys(
        item.strip() for item in grievance_ids if item.strip()
    ))

    if not ids:
        raise ValueError("Select at least one grievance.")

    if len(ids) > 500:
        raise ValueError("Maximum 500 records per operation.")

    placeholders = ",".join("?" for _ in ids)

    return _delete_matching_records(
        f"WHERE grievance_id IN ({placeholders})",
        tuple(ids)
    )


def delete_grievances_by_filters(
    department_code: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None
) -> dict:
    """Delete grievances matching specified filters."""

    conditions = []
    parameters = []

    if department_code:
        department_code = department_code.strip().upper()

        if department_code not in DEPARTMENTS:
            raise ValueError("Invalid department code.")

        conditions.append("department_code = ?")
        parameters.append(department_code)

    if status:
        status = status.strip().upper()

        if status not in ALLOWED_STATUSES:
            raise ValueError("Invalid grievance status.")

        conditions.append("status = ?")
        parameters.append(status)

    if date_from or date_to:
        for value in (date_from, date_to):
            if value:
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError as error:
                    raise ValueError(
                        "Dates must use YYYY-MM-DD format."
                    ) from error

    if date_from:
        conditions.append("date(registered_at) >= date(?)")
        parameters.append(date_from)

    if date_to:
        conditions.append("date(registered_at) <= date(?)")
        parameters.append(date_to)

    if not conditions:
        raise ValueError(
            "Select at least one filter. "
            "Use clear_all_grievances for a complete reset."
        )

    return _delete_matching_records(
        "WHERE " + " AND ".join(conditions),
        tuple(parameters)
    )


def clear_all_grievances() -> dict:
    """Permanently delete all grievances and associated documents."""

    return _delete_matching_records(
        "",
        (),
        reset_sequence=True
    )


# ============================================================
# END DATABASE MANAGEMENT OPERATIONS
# ============================================================


if __name__ == "__main__":

    init_db()

    print("Grievance database initialized successfully.")

    print(f"Database location: {DATABASE_PATH}")

    print(f"Document storage: {DEPARTMENT_STORAGE}")
