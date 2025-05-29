"""
Document Classification Agent using Gemini with robust fallbacks
"""

import asyncio
import os
from typing import Dict, Any
import logging
import google.generativeai as genai
from dotenv import load_dotenv

from models.schemas import DocumentType

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DocumentClassifierAgent:
    """
    Agent responsible for classifying uploaded documents into categories
    """
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('models/gemini-1.5-flash')
                self.gemini_available = True
                logger.info("✅ Gemini API configured successfully")
            except Exception as e:
                logger.error(f"❌ Failed to configure Gemini: {e}")
                self.gemini_available = False
        else:
            logger.warning("⚠️ No Gemini API key found, using fallback classification")
            self.gemini_available = False
        
        self.classification_prompt = """
        You are a medical document classifier. Analyze the filename and content to classify this document.
        
        This document may contain MULTIPLE types of medical documents. Classify based on the PRIMARY content.
        
        Document types to classify into:
        - bill: Medical bills, invoices, billing statements (look for amounts, charges, total cost)
        - discharge_summary: Hospital discharge summaries, medical summaries (look for diagnosis, admission/discharge dates)
        - id_card: Insurance cards, patient ID cards
        - prescription: Prescription forms, medication lists
        - lab_report: Laboratory test results, diagnostic reports
        - unknown: If unclear or doesn't fit other categories
        
        Filename: {filename}
        Content preview: {content_preview}
        
        Respond with JSON only:
        {{
            "document_type": "bill|discharge_summary|id_card|prescription|lab_report|unknown",
            "confidence": 0.0-1.0,
            "reasoning": "brief explanation"
        }}
        """
    
    async def classify_document(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a document based on filename and content with robust fallbacks
        """
        try:
            filename = file_info.get('filename', '')
            content_preview = file_info.get('content_preview', '')
            
            logger.info(f"🔍 Classifying document: {filename}")
            
            # First, try enhanced filename-based classification
            filename_classification = self._enhanced_classify_by_filename(filename)
            
            # If we have content, try content-based classification
            if content_preview:
                content_classification = self._classify_by_content_patterns(content_preview)
                
                # Combine filename and content classification
                if content_classification['confidence'] > filename_classification['confidence']:
                    best_classification = content_classification
                else:
                    best_classification = filename_classification
            else:
                best_classification = filename_classification
            
            # If high confidence from pattern matching, use it
            if best_classification['confidence'] > 0.7:
                logger.info(f"✅ High confidence classification: {best_classification['document_type']} ({best_classification['confidence']:.2f})")
                return best_classification
            
            # If Gemini is available and confidence is low, try Gemini
            if self.gemini_available:
                try:
                    gemini_classification = await self._classify_with_gemini(filename, content_preview)
                    if gemini_classification['confidence'] > best_classification['confidence']:
                        logger.info(f"🤖 Gemini improved classification: {gemini_classification['document_type']}")
                        return gemini_classification
                except Exception as e:
                    logger.error(f"❌ Gemini classification failed: {str(e)}")
            
            logger.info(f"📋 Final classification: {best_classification['document_type']} ({best_classification['confidence']:.2f})")
            return best_classification
                
        except Exception as e:
            logger.error(f"❌ Error classifying document {file_info.get('filename', 'unknown')}: {str(e)}")
            return {
                "document_type": DocumentType.UNKNOWN,
                "confidence": 0.0,
                "reasoning": f"Classification failed: {str(e)}"
            }
    
    def _enhanced_classify_by_filename(self, filename: str) -> Dict[str, Any]:
        """
        Enhanced filename-based classification with more patterns
        """
        filename_lower = filename.lower()
        
        patterns = {
            DocumentType.BILL: ['bill', 'invoice', 'receipt', 'payment', 'billing', 'charges', 'yashodha', 'yashoda'],
            DocumentType.DISCHARGE_SUMMARY: ['discharge', 'summary', 'hospital', 'admission'],
            DocumentType.ID_CARD: ['id', 'card', 'insurance', 'member'],
            DocumentType.PRESCRIPTION: ['prescription', 'rx', 'medication', 'drugs'],
            DocumentType.LAB_REPORT: ['lab', 'test', 'report', 'results', 'pathology']
        }
        
        for doc_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return {
                        "document_type": doc_type,
                        "confidence": 0.8,
                        "reasoning": f"Filename contains keyword: {keyword}"
                    }
        
        return {
            "document_type": DocumentType.UNKNOWN,
            "confidence": 0.3,
            "reasoning": "No clear filename patterns matched"
        }
    
    def _classify_by_content_patterns(self, content: str) -> Dict[str, Any]:
        """
        Classify based on content patterns - this is the key enhancement
        """
        content_lower = content.lower()
        
        # Bill indicators with scoring
        bill_indicators = [
            ('total amount', 3), ('bill of supply', 3), ('invoice', 2), ('gst', 2),
            ('net amount', 2), ('charges', 1), ('₹', 2), ('rs.', 1),
            ('patient diet', 1), ('doctor fees', 2), ('surgery package', 3),
            ('medical appliances', 2), ('cost of implants', 2)
        ]
        
        # Discharge summary indicators with scoring  
        discharge_indicators = [
            ('discharge summary', 4), ('admission', 2), ('diagnosis', 3),
            ('chief complaint', 2), ('history of present illness', 3),
            ('recommendations at discharge', 3), ('surgery', 2),
            ('patient was admitted', 2), ('bilateral total knee replacement', 3),
            ('chief consultants', 2), ('physical examination', 2)
        ]
        
        # Calculate scores
        bill_score = sum(weight for phrase, weight in bill_indicators if phrase in content_lower)
        discharge_score = sum(weight for phrase, weight in discharge_indicators if phrase in content_lower)
        
        logger.info(f"📊 Content analysis - Bill score: {bill_score}, Discharge score: {discharge_score}")
        
        # Determine classification
        if bill_score >= 5 and bill_score > discharge_score:
            confidence = min(0.7 + (bill_score * 0.05), 0.95)
            return {
                "document_type": DocumentType.BILL,
                "confidence": confidence,
                "reasoning": f"Strong billing content indicators (score: {bill_score})"
            }
        elif discharge_score >= 5 and discharge_score > bill_score:
            confidence = min(0.7 + (discharge_score * 0.05), 0.95)
            return {
                "document_type": DocumentType.DISCHARGE_SUMMARY,
                "confidence": confidence,
                "reasoning": f"Strong discharge summary indicators (score: {discharge_score})"
            }
        elif bill_score >= 3 or discharge_score >= 3:
            # If both are present but one is stronger, classify as the stronger one
            if bill_score >= discharge_score:
                return {
                    "document_type": DocumentType.BILL,
                    "confidence": 0.75,
                    "reasoning": f"Mixed document, stronger bill indicators ({bill_score} vs {discharge_score})"
                }
            else:
                return {
                    "document_type": DocumentType.DISCHARGE_SUMMARY,
                    "confidence": 0.75,
                    "reasoning": f"Mixed document, stronger discharge indicators ({discharge_score} vs {bill_score})"
                }
        else:
            return {
                "document_type": DocumentType.UNKNOWN,
                "confidence": 0.3,
                "reasoning": f"Insufficient content indicators (bill: {bill_score}, discharge: {discharge_score})"
            }
    
    async def _classify_with_gemini(self, filename: str, content_preview: str) -> Dict[str, Any]:
        """
        Use Gemini for classification when available
        """
        try:
            prompt = self.classification_prompt.format(
                filename=filename,
                content_preview=content_preview[:800]
            )
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            result_text = response.text.strip()
            
            # Clean up response
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            
            import json
            result = json.loads(result_text)
            
            doc_type = result.get('document_type', 'unknown')
            if doc_type not in [dt.value for dt in DocumentType]:
                doc_type = DocumentType.UNKNOWN
            
            return {
                "document_type": DocumentType(doc_type),
                "confidence": float(result.get('confidence', 0.5)),
                "reasoning": result.get('reasoning', 'Gemini classification')
            }
            
        except Exception as e:
            logger.error(f"❌ Gemini classification failed: {str(e)}")
            raise e
