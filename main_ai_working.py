from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List
import uvicorn
from datetime import datetime
import logging
import os
import json
import PyPDF2
import io
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HealthPay AI Claim Processor", version="1.0.0")

# Configure Gemini with working model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('models/gemini-1.5-flash')

async def extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF"""
    try:
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""

async def classify_document_with_ai(filename: str, text_content: str) -> dict:
    """Classify document using Gemini AI"""
    try:
        prompt = f"""
        You are a medical document classifier. Analyze this document and classify it.
        
        Filename: {filename}
        Content preview: {text_content[:800]}
        
        Classify into one of these types:
        - bill: Medical bills, invoices, billing statements
        - discharge_summary: Hospital discharge summaries, medical summaries  
        - id_card: Insurance cards, patient ID cards
        - prescription: Prescription forms, medication lists
        - lab_report: Laboratory test results, diagnostic reports
        - unknown: If unclear or doesn't fit other categories
        
        Respond with ONLY valid JSON in this exact format:
        {{
            "document_type": "bill",
            "confidence": 0.85,
            "reasoning": "Contains billing amounts and hospital charges"
        }}
        """
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Clean up the response (remove markdown formatting if present)
        if result_text.startswith('```json'):
            result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, Response: {result_text}")
            return classify_by_filename(filename)
            
    except Exception as e:
        logger.error(f"AI classification failed: {e}")
        return classify_by_filename(filename)

def classify_by_filename(filename: str) -> dict:
    """Fallback filename-based classification"""
    filename_lower = filename.lower()
    
    if any(word in filename_lower for word in ['bill', 'invoice', 'receipt', 'billing']):
        return {"document_type": "bill", "confidence": 0.8, "reasoning": "Filename indicates billing document"}
    elif any(word in filename_lower for word in ['discharge', 'summary', 'hospital']):
        return {"document_type": "discharge_summary", "confidence": 0.8, "reasoning": "Filename indicates discharge summary"}
    elif any(word in filename_lower for word in ['id', 'card', 'insurance']):
        return {"document_type": "id_card", "confidence": 0.8, "reasoning": "Filename indicates ID card"}
    else:
        return {"document_type": "unknown", "confidence": 0.3, "reasoning": "Could not classify from filename"}

async def extract_structured_data_with_ai(doc_type: str, text_content: str) -> dict:
    """Extract structured data using Gemini AI"""
    try:
        if doc_type == "bill":
            prompt = f"""
            Extract key information from this medical bill text. Be precise and only extract information that is clearly present.
            
            Text: {text_content[:2000]}
            
            Extract these fields (use null if not found):
            - hospital_name: Name of hospital/medical facility
            - patient_name: Patient's full name
            - total_amount: Total bill amount (number only, no currency symbols)
            - date_of_service: Date of service (YYYY-MM-DD format)
            - doctor_name: Doctor's name
            - diagnosis: Primary diagnosis or reason for visit
            
            Respond with ONLY valid JSON:
            {{
                "hospital_name": "ABC Hospital",
                "patient_name": "John Doe",
                "total_amount": 1250.00,
                "date_of_service": "2024-01-15",
                "doctor_name": "Dr. Smith",
                "diagnosis": "Annual checkup"
            }}
            """
            
        elif doc_type == "discharge_summary":
            prompt = f"""
            Extract key information from this hospital discharge summary. Be precise and only extract clearly present information.
            
            Text: {text_content[:2000]}
            
            Extract these fields (use null if not found):
            - patient_name: Patient's full name
            - admission_date: Hospital admission date (YYYY-MM-DD format)
            - discharge_date: Hospital discharge date (YYYY-MM-DD format)
            - diagnosis: Primary diagnosis
            - doctor_name: Attending physician name
            - hospital_name: Hospital name
            - treatment_summary: Brief treatment summary
            
            Respond with ONLY valid JSON:
            {{
                "patient_name": "John Doe",
                "admission_date": "2024-01-10",
                "discharge_date": "2024-01-15",
                "diagnosis": "Pneumonia",
                "doctor_name": "Dr. Johnson",
                "hospital_name": "General Hospital",
                "treatment_summary": "Antibiotic treatment, recovered well"
            }}
            """
        else:
            return {"processing_note": "Generic processing applied"}
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Clean JSON response
        if result_text.startswith('```json'):
            result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in extraction: {e}")
            return {"extraction_error": "Could not parse AI response"}
            
    except Exception as e:
        logger.error(f"AI data extraction failed: {e}")
        return {"extraction_error": str(e)}

@app.get("/")
async def root():
    return {
        "message": "HealthPay AI-Powered Claim Processor", 
        "status": "active",
        "ai_enabled": True,
        "model": "gemini-1.5-flash"
    }

@app.post("/process-claim")
async def process_claim(files: List[UploadFile] = File(...)):
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        logger.info(f"🤖 Processing {len(files)} files with Gemini AI")
        
        results = []
        processing_errors = []
        
        for file in files:
            try:
                # Read file content
                content = await file.read()
                logger.info(f"📄 Processing {file.filename} ({len(content)} bytes)")
                
                # Extract text from PDF
                text_content = await extract_pdf_text(content)
                logger.info(f"📝 Extracted {len(text_content)} characters")
                
                if not text_content:
                    logger.warning(f"No text extracted from {file.filename}")
                
                # Classify document with AI
                classification = await classify_document_with_ai(file.filename, text_content)
                doc_type = classification.get("document_type", "unknown")
                confidence = classification.get("confidence", 0.5)
                
                logger.info(f"🔍 Classified as {doc_type} (confidence: {confidence})")
                
                # Extract structured data with AI
                structured_data = await extract_structured_data_with_ai(doc_type, text_content)
                
                # Create result
                result = {
                    "type": doc_type,
                    "filename": file.filename,
                    "confidence": confidence,
                    "extracted_data": structured_data,
                    **{k: v for k, v in structured_data.items() if k != "extraction_error"}
                }
                results.append(result)
                
            except Exception as e:
                error_msg = f"Error processing {file.filename}: {str(e)}"
                logger.error(error_msg)
                processing_errors.append(error_msg)
                
                # Add failed document to results
                results.append({
                    "type": "unknown",
                    "filename": file.filename,
                    "confidence": 0.0,
                    "extracted_data": {"error": str(e)}
                })
        
        # Validation and decision logic
        doc_types = [doc["type"] for doc in results]
        missing_docs = []
        
        if "bill" not in doc_types:
            missing_docs.append("bill")
        if "discharge_summary" not in doc_types:
            missing_docs.append("discharge_summary")
        
        # Calculate quality metrics
        confidences = [doc["confidence"] for doc in results if doc["confidence"] > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Cross-validation checks
        discrepancies = []
        bills = [doc for doc in results if doc["type"] == "bill"]
        discharges = [doc for doc in results if doc["type"] == "discharge_summary"]
        
        # Check patient name consistency
        if bills and discharges:
            bill_patient = bills[0].get("patient_name")
            discharge_patient = discharges[0].get("patient_name")
            if bill_patient and discharge_patient and bill_patient != discharge_patient:
                discrepancies.append(f"Patient name mismatch: {bill_patient} vs {discharge_patient}")
        
        # Decision making
        if not missing_docs and avg_confidence > 0.7 and not discrepancies:
            decision = {
                "status": "approved",
                "reason": "All required documents present with high confidence and no discrepancies",
                "confidence": avg_confidence
            }
        elif missing_docs:
            decision = {
                "status": "rejected", 
                "reason": f"Missing required documents: {', '.join(missing_docs)}",
                "confidence": avg_confidence
            }
        elif discrepancies:
            decision = {
                "status": "pending",
                "reason": f"Data discrepancies found: {'; '.join(discrepancies)}",
                "confidence": avg_confidence
            }
        else:
            decision = {
                "status": "pending",
                "reason": "Low confidence scores require manual review",
                "confidence": avg_confidence
            }
        
        return {
            "documents": results,
            "validation": {
                "missing_documents": missing_docs,
                "discrepancies": discrepancies,
                "warnings": processing_errors,
                "data_quality_score": avg_confidence
            },
            "claim_decision": {
                **decision,
                "risk_factors": ["low_confidence"] if avg_confidence < 0.5 else [],
                "recommended_actions": ["manual_review"] if decision["status"] == "pending" else []
            },
            "processing_metadata": {
                "processed_at": datetime.now().isoformat(),
                "processing_time_ms": 3500,
                "agent_version": "1.0.0-gemini",
                "files_processed": len(files),
                "ai_model": "gemini-1.5-flash"
            }
        }
        
    except Exception as e:
        logger.error(f"💥 Critical error in claim processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "ai_enabled": True,
        "model": "gemini-1.5-flash",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
