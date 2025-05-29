import asyncio
import os
import json
import re
from typing import Dict, Any
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class BillProcessingAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        self.bill_prompt = """
        You are a medical billing specialist. Extract key information from this medical bill.
        
        Text: {text}
        
        Extract these fields precisely (use null if not found):
        - hospital_name: Hospital name
        - patient_name: Patient full name  
        - total_amount: Final total amount (number only)
        - date_of_service: Service date (YYYY-MM-DD format)
        - doctor_name: Doctor name
        - diagnosis: Primary diagnosis
        - registration_no: Patient registration number
        - episode_no: Episode number
        - room_charges: Room rent charges
        - medicine_charges: Total medicine costs
        
        Respond with ONLY valid JSON:
        {{
            "hospital_name": "string or null",
            "patient_name": "string or null",
            "total_amount": number or null,
            "date_of_service": "YYYY-MM-DD or null",
            "doctor_name": "string or null", 
            "diagnosis": "string or null",
            "registration_no": "string or null",
            "episode_no": "string or null",
            "room_charges": number or null,
            "medicine_charges": number or null,
            "confidence": 0.0-1.0
        }}
        """
    
    async def process_bill(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Process medical bill and extract structured data"""
        try:
            text = document.get('extracted_text', '')
            
            if not text.strip():
                return {"confidence": 0.0, "structured_data": {}, "error": "No text to process"}
            
            # Use Gemini for extraction
            gemini_result = await self._extract_with_gemini(text)
            
            # Enhance with regex patterns
            regex_result = self._extract_with_regex(text)
            
            # Combine results
            combined_data = self._combine_extraction_results(gemini_result, regex_result)
            
            return {
                "confidence": combined_data.get('confidence', 0.5),
                "structured_data": combined_data,
                "processing_method": "bill_agent_gemini_enhanced"
            }
            
        except Exception as e:
            logger.error(f"Bill processing failed: {str(e)}")
            return {"confidence": 0.0, "structured_data": {"error": str(e)}}
    
    async def _extract_with_gemini(self, text: str) -> Dict[str, Any]:
        """Extract bill data using Gemini"""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                self.bill_prompt.format(text=text[:3000])
            )
            
            result_text = response.text.strip()
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(result_text)
            return result
            
        except Exception as e:
            logger.error(f"Gemini bill extraction failed: {str(e)}")
            return {"confidence": 0.0}
    
    def _extract_with_regex(self, text: str) -> Dict[str, Any]:
        """Extract bill data using regex patterns"""
        result = {}
        
        # Enhanced amount patterns
        amount_patterns = [
            r'Total\s*:?\s*₹?\s*([\d,]+\.?\d*)',
            r'Net Payable\s*:?\s*₹?\s*([\d,]+\.?\d*)',
            r'FAMILY HEALTH PLAN.*?₹?\s*([\d,]+\.?\d*)',
            r'(\d{6}\.00)'  # 6-digit amounts
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    result['total_amount'] = float(matches[-1].replace(',', ''))
                    break
                except:
                    continue
        
        # Registration number
        reg_patterns = [r'Registration No\s*:?\s*(\d+)', r'Reg.*?No.*?(\d{7})']
        for pattern in reg_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['registration_no'] = match.group(1)
                break
        
        # Episode number  
        episode_match = re.search(r'Episode.*?:?\s*([A-Z\d]+)', text, re.IGNORECASE)
        if episode_match:
            result['episode_no'] = episode_match.group(1)
        
        result['confidence'] = 0.7 if len(result) > 2 else 0.3
        return result
    
    def _combine_extraction_results(self, gemini_result: Dict, regex_result: Dict) -> Dict[str, Any]:
        """Combine Gemini and regex results"""
        combined = gemini_result.copy()
        
        # Use regex as fallback/validation
        for key, value in regex_result.items():
            if key != 'confidence' and (not combined.get(key) or combined.get(key) is None):
                combined[key] = value
        
        # Calculate combined confidence
        gemini_conf = gemini_result.get('confidence', 0.0)
        regex_conf = regex_result.get('confidence', 0.0)
        combined['confidence'] = max(gemini_conf, (gemini_conf + regex_conf) / 2)
        
        return combined
