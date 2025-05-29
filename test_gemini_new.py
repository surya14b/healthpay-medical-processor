import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

try:
    # Configure Gemini
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Test with the newer API
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hello! Just respond with: API is working")
    
    print("✅ Gemini API is working!")
    print("Response:", response.text)
    
except Exception as e:
    print("❌ Gemini API error:", str(e))
    print("API Key starts with:", os.getenv("GEMINI_API_KEY", "")[:10] + "...")
