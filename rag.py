import os
import chromadb
import ollama
from pypdf import PdfReader
import json

# ---------- Settings ---------
DOCS_FOLDER = "documents"           # .txt, .md and .pdf files (and saved web pages)
DB_FOLDER = "chroma_db"             # the vector database is saved here
COLLECTION_NAME = "documents"
EMBED_MODEL = "embeddinggemma"    # turns text into numbers
CHAT_MODEL = "gemma4:e4b"           # writes the answer
CHUNK_SIZE = 800                    # characters in one chunk
CHUNK_OVERLAP = 150                 # characters shared by neighbouring chunks
TOP_K = 4                           # how many chunks we give to the model
EMBED_BATCH = 32                    # chunks sent to the embedding model at once
# Open (or create) the vector database on disk
client = chromadb.PersistentClient(path=DB_FOLDER)
def get_collection():
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        configuration={"hnsw": {"space": "cosine"}},  # measure closeness by angle
    )

# ---------- 1. Read files ---------
def read_file(path):

    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return (
            f"Title: {data.get('title', '')}\n"
            f"Source: {data.get('source', '')}\n\n"
            f"{data.get('content', '')}"
        )

    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    with open(path, encoding="utf-8") as file:
        return file.read()
    
def find_source(filename, text):
    if filename.lower().endswith(".json"):
        try:
            data = json.loads(text)
            return data.get("source", filename)
        except json.JSONDecodeError:
            return filename

    first_line = text.split("\n", 1)[0]

    if first_line.startswith("Source: "):
        return first_line[len("Source: "):].strip()

    return filename

# ---------- 2. Split text into chunks ---------
def split_into_chunks(text):
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + CHUNK_SIZE].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks

# ---------- 3. Turn text into embeddings (in small batches) ---------
def embed(texts):
    embeddings = []
    for i in range(0, len(texts), EMBED_BATCH):
        batch = texts[i:i + EMBED_BATCH]
        response = ollama.embed(model=EMBED_MODEL, input=batch)
        embeddings.extend(response["embeddings"])
    return embeddings

# ---------- 4. Ingest one file, or all files ---------
def index_file(filename):
    collection = get_collection()
    collection.delete(where={"file": filename})    # remove old chunks of this file
    text = read_file(os.path.join(DOCS_FOLDER, filename))
    chunks = split_into_chunks(text)
    if not chunks:
        return 0
    source = find_source(filename, text)
    collection.add(
        ids=[f"{filename}-{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embed(chunks),
        metadatas=[{"file": filename, "source": source} for _ in chunks],
    )
    print(f"Indexed {filename}: {len(chunks)} chunks")
    return len(chunks)

def index_documents():
    # Start fresh, so running ingest again does not create duplicates
    if COLLECTION_NAME in client.list_collections():
        client.delete_collection(name=COLLECTION_NAME)
    file_count = 0
    chunk_count = 0
    for filename in sorted(os.listdir(DOCS_FOLDER)):
        if not filename.lower().endswith((".json" , ".txt" , ".pdf")):
            continue
        added = index_file(filename)
        if added:
            file_count += 1
            chunk_count += added
    return {"files_indexed": file_count, "chunks_indexed": chunk_count}

def list_sources():
    collection = get_collection()
    counts = {}
    for meta in collection.get(include=["metadatas"])["metadatas"]:
        key = (meta["file"], meta["source"])
        counts[key] = counts.get(key, 0) + 1
    return [{"file": file, "source": source, "chunks": n}
            for (file, source), n in sorted(counts.items())]
# ---------- 5. Search: find the chunks closest to the question ---------
def search(question):
    collection = get_collection()
    if collection.count() == 0:
        return []
    results = collection.query(
        query_embeddings=embed([question]),
        n_results=min(TOP_K, collection.count()),
    )
    found = []
    for text, meta, distance in zip(results["documents"][0],
                                    results["metadatas"][0],
                                    results["distances"][0]):
        found.append({"source": meta["source"], "text": text,
                      "distance": round(distance, 3)})
    return found
# ---------- 6. Ask: search + build prompt + call the LLM ---------
def answer_question(question):
    chunks = search(question)
    if not chunks:
         return "No documents are indexed yet. Add a web page or call /ingest.", []
    context = "\n\n---\n\n".join(
        f"From {chunk['source']}:\n{chunk['text']}" for chunk in chunks
    )
    prompt = f"""Answer the question using ONLY the context below.
If the answer is not in the context, reply: "I don't know based on the given documents."
Keep the answer short and clear.
Context:
{context}
Question: {question}
Answer:"""
    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"], chunks