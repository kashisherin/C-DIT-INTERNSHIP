
import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Connect to Google Gemini API
client = genai.Client(api_key=api_key)

# Test Gemma 4
response = client.models.generate_content(
    model="gemma-4-26b-a4b-it",
    contents="Explain artificial intelligence in three simple sentences."
)

print("\nGemma 4 Cloud Response:\n")
print(response.text)
