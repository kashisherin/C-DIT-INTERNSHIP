import os
import base64
import requests

from io import BytesIO
from pathlib import Path

from PIL import Image
from dotenv import load_dotenv

from grievance import build_prompt

# Load existing project settings
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")

IMAGE_PATH = BASE_DIR /  "en_05_ration.jpg"


if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing.")

if not IMAGE_PATH.exists():
    raise FileNotFoundError(
        f"Test image not found: {IMAGE_PATH}"
    )

# Convert the original grievance image to PNG
image_buffer = BytesIO()

with Image.open(IMAGE_PATH) as image:
    image.convert("RGB").save(image_buffer, format="PNG")

image_bytes = image_buffer.getvalue()

# Encode image for REST API
encoded_image = base64.b64encode(
    image_bytes
).decode("utf-8")

prompt = build_prompt("English")

url = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
)

# Important: Image comes before text.
payload = {
    "contents": [{
        "role": "user",
        "parts": [
            {
                "inlineData": {
                    "mimeType": "image/png",
                    "data": encoded_image
                }
            },
            {
                "text": prompt
            }
        ]
    }],
    "generationConfig": {
        "temperature": 0,
        "topP": 0.8,
        "maxOutputTokens": 8192,
        "thinkingConfig": {
            "thinkingLevel": "MINIMAL"
        }
    }
}

print("Sending grievance image to Gemma 4...")
print("Model:", MODEL)

response = requests.post(
    url,
    params={"key": API_KEY},
    json=payload,
    timeout=180
)

print("\nHTTP status:", response.status_code)

if not response.ok:
    print("API error:", response.text)
    raise SystemExit(1)

data = response.json()

usage = data.get("usageMetadata", {})

print("Thought tokens:",
      usage.get("thoughtsTokenCount", 0))

print("Candidate tokens:",
      usage.get("candidatesTokenCount", 0))

print("Total tokens:",
      usage.get("totalTokenCount", 0))

candidates = data.get("candidates", [])

for candidate in candidates:
    print("Finish reason:", candidate.get("finishReason"))

    parts = candidate.get("content", {}).get("parts", [])

    result = "\n".join(
        part.get("text", "")
        for part in parts
        if part.get("text") and not part.get("thought", False)
    )

    print("\n========== GRIEVANCE OUTPUT ==========\n")
    print(result)
    print("\n======================================")