import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    
    # List available models
    print("📋 Available models:")
    for model in genai.list_models():
        print(f"  - {model.name}")
        
except Exception as e:
    print(f"❌ Error listing models: {e}")
