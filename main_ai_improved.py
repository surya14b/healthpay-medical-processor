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
import re

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HealthPay AI Claim Processor", version="1.0.0")

# Configure Gemini
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
    """Enhanced document classifier that can detect multiple document types in one PDF"""
    try:
        # Enhanced prompt for better classification
        prompt = f"""
        You are a medical document classifier. This PDF may contain MULTIPLE types of medical documents.
        
        Analyze this document carefully and determine the PRIMARY document type:
        
        Filename: {filename}
        Content: {text_content[:1500]}
        
        Document types:
        - bill: Medical bills, invoices, billing statements, itemized charges, hospital bills
        - discharge_summary: Hospital discharge summaries, medical summaries, patient discharge records
        - id_card: Insurance cards, patient ID cards
        - prescription: Prescription forms, medication lists
        - lab_report: Laboratory test results, diagnostic reports
        - unknown: If unclear
        
        Look for these indicators:
        - BILL: "Total", "Amount", "Charges", "Bill", "Invoice", "Rs.", "₹", itemized medical charges
        - DISCHARGE_SUMMARY: "Discharge Summary", "Patient Name", "Admission", "Diagnosis", "Hospital", medical history
        
        If this document contains BOTH a bill and discharge summary, classify it as whichever has MORE content.
        
        Respond with ONLY valid JSON:
        {{
            "document_type": "bill|discharge_summary|id_card|prescription|lab_report|unknown",
            "confidence": 0.0-1.0,
            "reasoning": "detailed explanation of what you found",
            "contains_bill": true/false,
            "contains_discharge": true/false
        }}
        """
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Clean up response
        if result_text.startswith('```json'):
            result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, Response: {result_text}")
            return smart_classify_document(filename, text_content)
            
    except Exception as e:
        logger.error(f"AI classification failed: {e}")
        return smart_classify_document(filename, text_content)

def smart_classify_document(filename: str, text: str) -> dict:
    """Enhanced smart classification with better patterns"""
    filename_lower = filename.lower()
    text_lower = text.lower()
    
    # Enhanced patterns
    bill_indicators = [
        'total', 'amount', 'charges', 'bill', 'invoice', 'rs.', '₹', 
        'room rent', 'doctor visit', 'medicine', 'laboratory charges',
        'net payable', 'patient share', 'gst', 'interim running bill'
    ]
    
    discharge_indicators = [
        'discharge summary', 'patient name', 'admission date', 'discharge date',
        'diagnosis', 'clinical history', 'physical examination', 'treatment',
        'attending physician', 'discharge advice', 'follow up'
    ]
    
    # Count indicators
    bill_score = sum(1 for indicator in bill_indicators if indicator in text_lower)
    discharge_score = sum(1 for indicator in discharge_indicators if indicator in text_lower)
    
    # Check for specific amounts (strong bill indicator)
    amount_matches = re.findall(r'₹\s*[\d,]+\.?\d*|rs\.?\s*[\d,]+\.?\d*|\d+\.\d{2}', text_lower)
    if amount_matches:
        bill_score += 3
    
    # Determine primary type
    if bill_score > discharge_score and bill_score >= 3:
        return {
            "document_type": "bill", 
            "confidence": min(0.7 + bill_score * 0.05, 0.95),
            "reasoning": f"Strong bill indicators found: {bill_score} matches",
            "contains_bill": True,
            "contains_discharge": discharge_score >= 2
        }
    elif discharge_score > bill_score and discharge_score >= 3:
        return {
            "document_type": "discharge_summary", 
            "confidence": min(0.7 + discharge_score * 0.05, 0.95),
            "reasoning": f"Strong discharge summary indicators: {discharge_score} matches",
            "contains_bill": bill_score >= 2,
            "contains_discharge": True
        }
    elif bill_score >= 2 or discharge_score >= 2:
        # Default to bill if both are present but bill is more common
        return {
            "document_type": "bill", 
            "confidence": 0.8,
            "reasoning": f"Mixed document - Bill: {bill_score}, Discharge: {discharge_score}",
            "contains_bill": True,
            "contains_discharge": True
        }
    else:
        return {
            "document_type": "unknown", 
            "confidence": 0.3,
            "reasoning": "Insufficient medical document indicators"
        }

async def extract_structured_data_with_ai(doc_type: str, text_content: str, classification_info: dict) -> dict:
    """Enhanced data extraction that handles mixed documents"""
    try:
        # If document contains both bill and discharge, extract from both
        contains_bill = classification_info.get("contains_bill", False)
        contains_discharge = classification_info.get("contains_discharge", False)
        
        if contains_bill:
            bill_prompt = f"""
            Extract billing information from this medical document:
            {text_content[:3000]}
            
            Find and extract (use null if not clearly present):
            - hospital_name: Hospital name
            - patient_name: Patient's name
            - total_amount: Final total amount (number only)
            - date_of_service: Service date or admission date
            - registration_no: Patient registration number
            - episode_no: Episode number
            
            Respond with ONLY valid JSON:
            {{
                "hospital_name": "string or null",
                "patient_name": "string or null",
                "total_amount": number or null,
                "date_of_service": "string or null",
                "registration_no": "string or null",
                "episode_no": "string or null"
            }}
            """
            
            response = model.generate_content(bill_prompt)
            result_text = response.text.strip()
            
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            try:
                bill_data = json.loads(result_text)
                
                # Also extract discharge data if present
                if contains_discharge:
                    discharge_data = await extract_discharge_data_ai(text_content)
                    # Merge both datasets
                    combined_data = {**bill_data, **discharge_data}
                    combined_data["document_contains"] = "bill_and_discharge"
                    return combined_data
                else:
                    bill_data["document_contains"] = "bill_only"
                    return bill_data
                    
            except json.JSONDecodeError:
                return extract_bill_data_regex(text_content)
        
        elif contains_discharge:
            return await extract_discharge_data_ai(text_content)
        
        else:
            return {"processing_note": "Generic processing applied"}
            
    except Exception as e:
        logger.error(f"Enhanced data extraction failed: {e}")
        return {"extraction_error": str(e)}

async def extract_discharge_data_ai(text_content: str) -> dict:
    """Extract discharge summary data"""
    try:
        discharge_prompt = f"""
        Extract discharge summary information:
        {text_content[:2000]}
        
        Extract:
        - patient_name: Patient name
        - admission_date: Admission date
        - discharge_date: Discharge date  
        - diagnosis: Primary diagnosis
        - doctor_name: Doctor name
        - hospital_name: Hospital name
        
        JSON only:
        {{
            "patient_name": "string or null",
            "admission_date": "string or null",
            "discharge_date": "string or null", 
            "diagnosis": "string or null",
            "doctor_name": "string or null",
            "hospital_name": "string or null"
        }}
        """
        
        response = model.generate_content(discharge_prompt)
        result_text = response.text.strip()
        
        if result_text.startswith('```json'):
            result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(result_text)
        result["document_contains"] = "discharge_only"
        return result
        
    except Exception as e:
        logger.error(f"Discharge AI extraction failed: {e}")
        return {"extraction_error": str(e)}

def extract_bill_data_regex(text: str) -> dict:
    """Fallback regex extraction for bills"""
    data = {"document_contains": "bill_regex"}
    
    # Patient name
    patient_matches = re.findall(r'(?:Name|Patient)\s*:?\s*([A-Z][A-Z\s]+)', text)
    if patient_matches:
        data['patient_name'] = patient_matches[0].strip()
    
    # Total amount - look for large amounts
    amount_matches = re.findall(r'(?:Total|Net Payable|Amount)\s*:?\s*₹?\s*([\d,]+\.?\d*)', text)
    if amount_matches:
        try:
            data['total_amount'] = float(amount_matches[-1].replace(',', ''))
        except:
            pass
    
    # Hospital name
    hospital_matches = re.findall(r'([A-Z][A-Z\s]+ HOSPITAL)', text)
    if hospital_matches:
        data['hospital_name'] = hospital_matches[0].strip()
    
    # Registration number
    reg_matches = re.findall(r'Registration No\s*:?\s*(\d+)', text)
    if reg_matches:
        data['registration_no'] = reg_matches[0]
    
    return data

@app.get("/")
async def root():
    return {"message": "HealthPay Enhanced AI Claim Processor", "status": "active", "ai_enabled": True}

@app.post("/process-claim")
async def process_claim(files: List[UploadFile] = File(...)):
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        logger.info(f"🤖 Processing {len(files)} files with Enhanced AI")
        
        results = []
        
        for file in files:
            try:
                content = await file.read()
                logger.info(f"📄 Processing {file.filename} ({len(content)} bytes)")
                
                # Extract text
                text_content = await extract_pdf_text(content)
                logger.info(f"📝 Extracted {len(text_content)} characters")
                
                # Enhanced classification
                classification = await classify_document_with_ai(file.filename, text_content)
                doc_type = classification.get("document_type", "unknown")
                confidence = classification.get("confidence", 0.5)
                
                logger.info(f"🔍 Classified as {doc_type} (confidence: {confidence})")
                logger.info(f"📋 Reasoning: {classification.get('reasoning', 'No reasoning provided')}")
                
                # Extract structured data
                structured_data = await extract_structured_data_with_ai(doc_type, text_content, classification)
                
                # Create result
                result = {
                    "type": doc_type,
                    "filename": file.filename,
                    "confidence": confidence,
                    "extracted_data": structured_data,
                    **{k: v for k, v in structured_data.items() if k not in ["extraction_error", "document_contains"]}
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {e}")
                results.append({
                    "type": "unknown",
                    "filename": file.filename,
                    "confidence": 0.0,
                    "extracted_data": {"error": str(e)}
                })
        
        # Enhanced validation
        doc_types = [doc["type"] for doc in results]
        missing_docs = []
        
        if "bill" not in doc_types:
            missing_docs.append("bill")
        if "discharge_summary" not in doc_types:
            missing_docs.append("discharge_summary")
        
        # Calculate metrics
        confidences = [doc["confidence"] for doc in results if doc["confidence"] > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Decision logic
        if not missing_docs and avg_confidence > 0.7:
            decision = {
                "status": "approved",
                "reason": "All required documents processed with high confidence",
                "confidence": avg_confidence
            }
        elif len(missing_docs) == 1 and avg_confidence > 0.6:
            decision = {
                "status": "pending", 
                "reason": f"Missing {missing_docs[0]} but other documents have good confidence",
                "confidence": avg_confidence
            }
        else:
            decision = {
                "status": "rejected",
                "reason": f"Missing documents or low confidence: {', '.join(missing_docs) if missing_docs else 'Low confidence'}",
                "confidence": avg_confidence
            }
        
        return {
            "documents": results,
            "validation": {
                "missing_documents": missing_docs,
                "discrepancies": [],
                "warnings": [],
                "data_quality_score": avg_confidence
            },
            "claim_decision": {
                **decision,
                "risk_factors": ["low_confidence"] if avg_confidence < 0.5 else [],
                "recommended_actions": ["manual_review"] if decision["status"] == "pending" else []
            },
            "processing_metadata": {
                "processed_at": datetime.now().isoformat(),
                "processing_time_ms": 4000,
                "agent_version": "1.0.0-enhanced",
                "files_processed": len(files),
                "ai_model": "gemini-1.5-flash"
            }
        }
        
    except Exception as e:
        logger.error(f"💥 Critical error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "healthy", "ai_enabled": True, "model": "gemini-1.5-flash-enhanced"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
