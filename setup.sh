#!/bin/bash
echo "🚀 Creating HealthPay Claim Processor files..."
mkdir -p agents models utils tests uploads logs
touch agents/__init__.py models/__init__.py utils/__init__.py tests/__init__.py

cat > .env << 'ENVEOF'
GEMINI_API_KEY=your_gemini_key_here
UPLOAD_DIR=./uploads
LOG_LEVEL=INFO
ENVEOF

cat > requirements.txt << 'REQEOF'
fastapi==0.95.2
uvicorn[standard]==0.22.0
python-multipart==0.0.6
pydantic==1.10.12
google-generativeai==0.1.0rc2
PyPDF2==3.0.1
PyMuPDF==1.22.5
Pillow==9.5.0
python-dotenv==1.0.0
REQEOF

echo "✅ Basic files created!"
echo "📝 Now creating Python files..."
