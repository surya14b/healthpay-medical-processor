import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Test Gemini connection
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Try the older API format
    response = genai.generate_text(
        model="models/text-bison-001",
        prompt="Hello, can you classify this as a test? Respond with: {'status': 'working', 'message': 'Gemini is connected'}"
    )
    print("✅ Gemini API is working!")
    print("Response:", response.result if hasattr(response, 'result') else response)
    
except Exception as e:
    print("❌ Gemini API error:", str(e))
    print("Please check your API key in the .env file")
