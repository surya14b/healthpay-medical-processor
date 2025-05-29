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

The system follows a clean, modular pipeline of agents:

[Upload Endpoint]
↓
[Async PDF Handler]
↓
[OCR Agent]
↓
[Extraction Agent]
↓
[Validation Agent]
↓
[Summarization Agent]
↓
[Final Processed Response]


### 🧩 Component Responsibilities

- **FastAPI**: Serves the backend API and handles upload requests.
- **Async Upload Handler**: Accepts multiple PDF files using async `UploadFile`.
- **OCR Agent**: Extracts text from scanned PDFs using OCR.
- **Extraction Agent**: Uses AI to pull structured data like:
  - Patient Name
  - Admission/Discharge Dates
  - Hospital Name
  - Charges
- **Validation Agent**: Compares documents for consistency across key fields.
- **Summarization Agent**: Outputs a final summary or report based on results.

---

## 🤖 AI Tools Used

| Tool            | Purpose                                      |
|-----------------|----------------------------------------------|
| Google Gemini   | Natural language understanding & extraction  |
| LangChain       | Agent orchestration pipeline                 |
| PyMuPDF/OCR     | Text extraction from PDFs                    |

AI is used for:
- Named Entity Recognition (NER) for structured field extraction
- Semantic consistency validation across documents
- Summarization of the final output

---

## 💬 Prompt Examples Used

### 📥 Prompt 1 — PDF Upload & Orchestration

> "Create a FastAPI endpoint that accepts multiple PDF uploads and processes them through an agent orchestration pipeline. Use async processing where appropriate and implement proper error handling."

**Implemented:**
- `POST /process-documents` route in FastAPI
- Asynchronous file handling with `UploadFile`
- Orchestrated agent pipeline: OCR → Extraction → Validation → Summary
- Error handling for invalid or unsupported formats

---

### 🔍 Prompt 2 — Document Consistency Validator

> "Build a validation agent that cross-checks data consistency between medical bills and discharge summaries. Check for patient name matches, date consistency, and hospital name alignment."

**Implemented:**
- Validates:
  - Patient names
  - Dates (admission/discharge)
  - Hospital/clinic names
- Flags inconsistencies for review
- Supports insurance claim fraud detection

---

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **AI/NLP**: Google Gemini, LangChain
- **PDF Parsing**: PyMuPDF (`fitz`), pytesseract (optional)
- **Containerization**: Docker, Docker Compose
- **Language**: Python 3.11+

---

## 🧪 How to Run Locally

1. **Clone the Repository**

   ```bash
   git clone https://github.com/surya14b/healthpay-medical-processor.git
   cd healthpay-medical-processor
   
2.**Set Up Environment Variables**

 ```bash
cp .env.example .env
```
Open .env and add your Google Gemini API key and other required variables.

3.__Build and Start the App__

```bash
docker-compose up --build
```

4.__Access the API Docs__
Open your browser and go to:
http://localhost:8000/docs
