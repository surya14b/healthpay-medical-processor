# HealthPay AI-Driven Claim Document Processor

A sophisticated backend system that processes medical insurance claim documents using AI-powered multi-agent workflows. Built with FastAPI and leveraging Google Gemini for document classification, text extraction, and intelligent claim decision-making.

## 🏗️ Architecture Overview

### Multi-Agent System Design

The system implements a **modular multi-agent architecture** where specialized AI agents handle different aspects of claim processing:

📄 Upload → 🔍 Classify → 📝 Extract → 🤖 Process → ✅ Validate → 🎯 Decide

### Agent Workflow

1. **DocumentClassifierAgent**: Classifies uploaded PDFs (bill, discharge summary, ID card, etc.)
2. **TextExtractionAgent**: Extracts text using PyPDF2, PyMuPDF, and Gemini Vision API
3. **Specialized Processing Agents**:
   - **BillProcessingAgent**: Extracts billing information (amounts, dates, hospital names)
   - **DischargeProcessingAgent**: Processes medical summaries (diagnoses, treatment details)
4. **ValidationAgent**: Cross-validates data consistency across documents
5. **DecisionAgent**: Makes final approval/rejection decisions with confidence scoring

### Technology Stack

- **Backend Framework**: FastAPI with async support
- **AI/LLM Integration**: Google Gemini 1.5-Flash for document processing
- **Document Processing**: PyPDF2, PyMuPDF for PDF handling
- **Data Validation**: Pydantic models with comprehensive validation
- **File Handling**: Secure multipart file upload with validation

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API key (free from https://aistudio.google.com/app/apikey)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd healthpay-claim-processor

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Gemini API key