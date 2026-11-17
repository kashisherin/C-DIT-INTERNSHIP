import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing.")

MODEL = "gemma-4-26b-a4b-it"

url = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
)

payload = {
    "contents": [{
        "parts": [{
            "text": "Reply with exactly: OK"
        }]
    }],
    "generationConfig": {
        "temperature": 0,
        "maxOutputTokens": 512,
        "thinkingConfig": {
            "thinkingLevel": "MINIMAL"
        }
    }
}

response = requests.post(
    url,
    params={"key": API_KEY},
    json=payload,
    timeout=90
)

print("HTTP status:", response.status_code)

if not response.ok:
    print("API error:", response.text)
    raise SystemExit(1)

data = response.json()

for candidate in data.get("candidates", []):
    for part in candidate.get("content", {}).get("parts", []):
        if not part.get("thought", False):
            print("Response:", part.get("text", ""))

usage = data.get("usageMetadata", {})

print("Thought tokens:", usage.get("thoughtsTokenCount", 0))
print("Candidate tokens:", usage.get("candidatesTokenCount", 0))
print("Total tokens:", usage.get("totalTokenCount", 0))

for candidate in data.get("candidates", []):
    print("Finish reason:", candidate.get("finishReason"))