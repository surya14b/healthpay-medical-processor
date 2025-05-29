import asyncio
import os
import json
import re
from typing import Dict, Any
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class DischargeProcessingAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        self.discharge_prompt = """
        You are a medical records specialist. Extract information from this discharge summary.
        
        Text: {text}
        
        Extract these fields (use null if not found):
        - patient_name: Patient full name
        - admission_date: Admission date (YYYY-MM-DD)
        - discharge_date: Discharge date (YYYY-MM-DD) 
        - diagnosis: Primary diagnosis
        - secondary_diagnoses: List of secondary diagnoses
        - doctor_name: Attending physician
        - hospital_name: Hospital name
        - treatment_summary: Brief treatment summary
        - discharge_condition: Patient condition at discharge
        - follow_up_instructions: Follow-up care instructions
        
        Respond with ONLY valid JSON:
        {{
            "patient_name": "string or null",
            "admission_date": "YYYY-MM-DD or null",
            "discharge_date": "YYYY-MM-DD or null",
            "diagnosis": "string or null", 
            "secondary_diagnoses": ["list"],
            "doctor_name": "string or null",
            "hospital_name": "string or null",
            "treatment_summary": "string or null",
            "discharge_condition": "string or null",
            "follow_up_instructions": "string or null",
            "confidence": 0.0-1.0
        }}
        """
    
    async def process_discharge_summary(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Process discharge summary and extract structured data"""
        try:
            text = document.get('extracted_text', '')
            
            if not text.strip():
                return {"confidence": 0.0, "structured_data": {}}
            
            # Extract with Gemini
            gemini_result = await self._extract_with_gemini(text)
            
            # Enhance with medical patterns
            enhanced_result = self._enhance_medical_extraction(text, gemini_result)
            
            return {
                "confidence": enhanced_result.get('confidence', 0.5),
                "structured_data": enhanced_result,
                "processing_method": "discharge_agent_gemini"
            }
            
        except Exception as e:
            logger.error(f"Discharge processing failed: {str(e)}")
            return {"confidence": 0.0, "structured_data": {"error": str(e)}}
    
    async def _extract_with_gemini(self, text: str) -> Dict[str, Any]:
        """Extract discharge data using Gemini"""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                self.discharge_prompt.format(text=text[:4000])
            )
            
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(result_text)
            return result
            
        except Exception as e:
            logger.error(f"Gemini discharge extraction failed: {str(e)}")
            return {"confidence": 0.0}
    
    def _enhance_medical_extraction(self, text: str, gemini_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance with medical-specific patterns"""
        enhanced = gemini_result.copy()
        
        # Extract dates if missing
        if not enhanced.get('admission_date') or not enhanced.get('discharge_date'):
            date_patterns = [
                r'Admission.*?:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'Discharge.*?:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}-\w{3}-\d{2})'  # Format like 3-Feb-25
            ]
            
            dates_found = []
            for pattern in date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                dates_found.extend(matches)
            
            if len(dates_found) >= 2:
                enhanced['admission_date'] = dates_found[0]
                enhanced['discharge_date'] = dates_found[1]
            elif len(dates_found) == 1:
                enhanced['admission_date'] = dates_found[0]
        
        # Extract diagnosis if missing
        if not enhanced.get('diagnosis'):
            diagnosis_patterns = [
                r'DIAGNOSIS[:\s]+([^\n]+)',
                r'Primary Diagnosis[:\s]+([^\n]+)',
                r'Principal Diagnosis[:\s]+([^\n]+)'
            ]
            
            for pattern in diagnosis_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    enhanced['diagnosis'] = match.group(1).strip()
                    break
        
        # Boost confidence if medical patterns found
        if enhanced.get('diagnosis') or enhanced.get('admission_date'):
            current_conf = enhanced.get('confidence', 0.0)
            enhanced['confidence'] = min(current_conf + 0.2, 1.0)
        
        return enhanced
