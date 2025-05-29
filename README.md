# 🏥 HealthPay Medical Processor

An AI-powered FastAPI backend to automate the processing and validation of medical documents like bills and discharge summaries. Built with a modular, agent-based architecture using asynchronous file handling and AI integrations for intelligent extraction and consistency checking.

---

## 🚀 Features

- 📄 Upload multiple medical PDFs (bills, discharge summaries)
- 🤖 Agent-based processing pipeline (OCR → Extraction → Validation → Summarization)
- ✅ Cross-document validation for name/date/hospital consistency
- ⚡ Async FastAPI endpoints for fast uploads & processing
- 📦 Dockerized for easy deployment

---

## 🧠 Architecture & Logic

The system is structured as a modular pipeline of agents:

[Upload Endpoint] --> [Async PDF Handler] --> [OCR Agent] -->
[Extraction Agent] --> [Validation Agent] --> [Summarization Agent]
--> [Final Processed Response]


### 🧩 Component Responsibilities

- **FastAPI**: Serves the backend API endpoints.
- **Async Upload Handler**: Accepts multiple PDF files concurrently using `UploadFile`.
- **OCR Agent**: Converts PDF images to text using OCR techniques.
- **Extraction Agent**: Applies NER to extract structured fields such as:
  - Patient Name
  - Admission & Discharge Dates
  - Hospital Name
  - Total Charges
- **Validation Agent**: Cross-checks documents for consistency.
- **Summarization Agent**: Generates a user-friendly summary or discrepancy report.

---

## 🤖 AI Tools Used

| Tool            | Purpose                                      |
|-----------------|----------------------------------------------|
| Google Gemini   | Natural language understanding & extraction  |
| LangChain       | Agent orchestration pipeline                 |
| PyMuPDF/OCR     | Text extraction from PDFs                    |

AI is used in:

- Named Entity Recognition (NER) for structured data extraction
- Semantic validation across documents
- Intelligent summarization of processed output

---

## 💬 Prompt Examples Used

### 📥 Prompt 1 — PDF Upload & Orchestration

> **"Create a FastAPI endpoint that accepts multiple PDF uploads and processes them through an agent orchestration pipeline. Use async processing where appropriate and implement proper error handling."**

**Implemented:**
- `POST /process-documents` endpoint in FastAPI
- Async file handling with `UploadFile`
- Orchestration: OCR → Extraction → Validation → Summary
- Structured error handling

---

### 🔍 Prompt 2 — Document Consistency Validator

> **"Build a validation agent that cross-checks data consistency between medical bills and discharge summaries. Check for patient name matches, date consistency, and hospital name alignment."**

**Implemented:**
- Validates:
  - Patient name
  - Admission/discharge dates
  - Hospital name
- Returns detailed discrepancy report
- Useful for claim validation and fraud detection

---

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **AI/NLP**: Google Gemini, LangChain
- **PDF Parsing**: PyMuPDF (`fitz`), `pytesseract` (optional)
- **Containerization**: Docker, Docker Compose
- **Language**: Python 3.11+

---

## 🧪 How to Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/surya14b/healthpay-medical-processor.git
cd healthpay-medical-processor

2.Set Up Environment Variables

cp .env.example .env
Fill in your Google Gemini API key and any other required secrets.

3. Build and Start the App

docker-compose up --build