HealthPay Medical Processor
An AI-powered backend system designed to streamline the processing of medical insurance claim documents. Utilizing a multi-agent architecture, this system automates the extraction, validation, and summarization of information from medical bills and discharge summaries.

🧠 Architecture & Logic
Overview
The system is structured around a modular, multi-agent pipeline that processes uploaded PDF documents asynchronously. The primary components include:

FastAPI Backend: Handles API requests and manages asynchronous file uploads.

Document Processing Agents: Specialized agents for OCR, data extraction, validation, and summarization.

AI Models: Leveraging Google Gemini for natural language understanding and information extraction.

Validation Mechanisms: Ensures data consistency across documents.

Dockerized Deployment: Facilitates easy setup and scalability.

Workflow
File Upload: Users upload multiple PDF files via a FastAPI endpoint.

Asynchronous Processing: Uploaded files are processed asynchronously to optimize performance.

Agent Orchestration:

OCR Agent: Extracts text from PDFs.

Extraction Agent: Identifies and extracts relevant data fields.

Validation Agent: Cross-verifies data consistency between documents.

Summarization Agent: Generates concise summaries of the extracted information.

Response Generation: Processed data is compiled and returned to the user.

🤖 AI Tools & Technologies
Google Gemini: Utilized for advanced natural language processing tasks, including information extraction and summarization.

FastAPI: Serves as the web framework for handling API requests and managing asynchronous operations.

Docker: Ensures consistent and scalable deployment across different environments.

🧪 Example Prompts Used
Prompt 1
"Create a FastAPI endpoint that accepts multiple PDF uploads and processes them through an agent orchestration pipeline. Use async processing where appropriate and implement proper error handling."

Implementation Highlights:

Defined an asynchronous FastAPI endpoint to handle multiple file uploads.

Integrated error handling to manage exceptions during file processing.

Orchestrated the processing pipeline to handle each file through the defined agents.

Prompt 2
"Build a validation agent that cross-checks data consistency between medical bills and discharge summaries. Check for patient name matches, date consistency, and hospital name alignment."

Implementation Highlights:

Developed a validation agent that:

Extracts key fields such as patient name, admission/discharge dates, and hospital names from both documents.

Compares these fields to identify discrepancies.

Flags inconsistencies for further review.

🛠️ Setup & Installation
Clone the Repository:

bash
Copy
Edit
git clone https://github.com/surya14b/healthpay-medical-processor.git
cd healthpay-medical-processor
Set Up Environment Variables:

Rename .env.example to .env and populate it with the necessary configurations, including API keys for Google Gemini.

Build and Run with Docker:

bash
Copy
Edit
docker-compose up --build
Access the API:

The FastAPI application will be available at http://localhost:8000.

📂 Project Structure
css
Copy
Edit
├── agents/
│   ├── ocr_agent.py
│   ├── extraction_agent.py
│   ├── validation_agent.py
│   └── summarization_agent.py
├── models/
│   └── schemas.py
├── utils/
│   └── helpers.py
├── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
✅ Features
Asynchronous File Processing: Efficient handling of multiple file uploads.

Modular Agent Design: Each agent performs a specific task, enhancing maintainability.

Robust Validation: Ensures data integrity across different document types.

Scalable Deployment: Dockerized setup allows for easy scaling and deployment.