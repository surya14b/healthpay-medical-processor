# 🏥 HealthPay Medical Processor

An AI-powered FastAPI backend to automate processing and validation of medical documents like bills and discharge summaries. Designed using a modular, agent-based architecture with asynchronous file handling and AI integrations for intelligent extraction and consistency checking.

---

## 🚀 Features

- 📄 Upload multiple medical PDFs (bills, discharge summaries)
- 🤖 Agent-based processing pipeline (OCR → Extraction → Validation → Summarization)
- ✅ Cross-document validation for name/date/hospital consistency
- ⚡ Async FastAPI endpoints for fast uploads & processing
- 📦 Dockerized for easy deployment

---

## 🧠 Architecture & Logic

```mermaid
flowchart LR
    A[FastAPI Upload Endpoint] --> B[Async PDF Handler]
    B --> C[OCR Agent]
    C --> D[Extraction Agent]
    D --> E[Validation Agent]
    E --> F[Summarization Agent]
    F --> G[Processed Response]
FastAPI is used to build the API server and handle concurrent uploads.

Asynchronous processing ensures the server remains responsive under load.

Agent pipeline breaks down processing into clean, testable components:

OCR Agent: Converts PDF pages to text.

Extraction Agent: Uses NLP to identify structured info (patient name, dates, hospital, charges).

Validation Agent: Compares extracted data across documents for consistency.

Summarization Agent: Returns a concise and user-friendly summary.

🤖 AI Tools Used
Tool	Purpose
Google Gemini	Natural language understanding & extraction
LangChain	Agent orchestration pipeline
PyMuPDF / OCR	Text extraction from PDFs

AI is used primarily in:

Named entity recognition (NER) for data extraction

Semantic validation across documents

Intelligent summarization of the final output

💬 Prompt Examples Used
📥 Prompt 1 — PDF Upload & Orchestration
"Create a FastAPI endpoint that accepts multiple PDF uploads and processes them through an agent orchestration pipeline. Use async processing where appropriate and implement proper error handling."

✔️ Implemented:

POST /process-documents route in FastAPI

Async file handling using UploadFile

Agent orchestration pipeline: OCR → Extraction → Validation → Summary

Structured error handling for unsupported formats and failures

🔍 Prompt 2 — Document Consistency Validator
"Build a validation agent that cross-checks data consistency between medical bills and discharge summaries. Check for patient name matches, date consistency, and hospital name alignment."

✔️ Implemented:

Agent compares:

Patient name

Admission/discharge dates

Hospital/clinic names

Returns discrepancies for user action

Useful for flagging fraudulent or mismatched claims

🛠️ Tech Stack
Backend: FastAPI

AI/NLP: Google Gemini, LangChain

PDF Parsing: PyMuPDF (fitz), pytesseract (optional)

Containerization: Docker, Docker Compose

Language: Python 3.11+

🧪 How to Run Locally
Clone the repository

bash
Copy
Edit
git clone https://github.com/surya14b/healthpay-medical-processor.git
cd healthpay-medical-processor
Set up environment variables

bash
Copy
Edit
cp .env.example .env
# Fill in your Google Gemini API key and other secrets
Build & start with Docker

bash
Copy
Edit
docker-compose up --build
Access the API

Visit: http://localhost:8000/docs for Swagger UI

🗂️ Project Structure
bash
Copy
Edit
healthpay-medical-processor/
│
├── agents/
│   ├── ocr_agent.py
│   ├── extraction_agent.py
│   ├── validation_agent.py
│   └── summarization_agent.py
│
├── models/
│   └── schemas.py
│
├── utils/
│   └── helpers.py
│
├── main.py              # FastAPI app
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
