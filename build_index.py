
import os
from pathlib import Path

# Always use Gemini for the grievance deployment index.
os.environ["RAG_EMBED_PROVIDER"] = "gemini"

# Store the grievance index separately.
BASE_DIR = Path(__file__).resolve().parent
GRIEVANCE_DB_DIR = BASE_DIR / "chroma_db_deploy"

os.environ["GRIEVANCE_DB_FOLDER"] = str(GRIEVANCE_DB_DIR)

# Import only after setting environment variables.
from rag import index_grievance_database, get_grievance_collection


def main():
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to your local .env file."
        )

    print("Starting grievance database indexing...")
    print("Embedding provider: Gemini")
    print(f"Source database: {BASE_DIR / 'database' / 'grievances.db'}")
    print(f"Index location: {GRIEVANCE_DB_DIR}")

    result = index_grievance_database()

    collection = get_grievance_collection()
    total_chunks = collection.count()

    print("\nGrievance indexing completed.")
    print(f"Records indexed: {result['records_indexed']}")
    print(f"Chunks indexed: {result['chunks_indexed']}")
    print(f"Total chunks in collection: {total_chunks}")

    if total_chunks == 0:
        raise RuntimeError("No grievance records were indexed.")

    if total_chunks != result["chunks_indexed"]:
        raise RuntimeError(
            "The indexed chunk count does not match the reported count."
        )


if __name__ == "__main__":
    main()
