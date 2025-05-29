"""
Text Extraction Agent using multiple methods
"""

import asyncio
import os
from typing import Dict, Any
import logging
import PyPDF2
import io
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF for better PDF handling

logger = logging.getLogger(__name__)

class TextExtractionAgent:
    """
    Agent responsible for extracting text from documents using multiple methods
    """
    
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.gemini_model = genai.GenerativeModel('models/gemini-pro-vision')
        
        self.extraction_prompt = """
        Extract all visible text from this medical document image. 
        Focus on:
        - Patient information
        - Medical details
        - Dates and amounts
        - Doctor/Hospital names
        - Any structured data
        
        Return the extracted text in a clear, organized format.
        """
    
    async def extract_text(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract text from document using multiple extraction methods
        """
        try:
            file_path = document.get('file_path')
            filename = document.get('filename', '')
            
            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Try multiple extraction methods
            extraction_results = []
            
            # Method 1: PyPDF2 for basic text extraction
            pdf_text = await self._extract_with_pypdf2(file_path)
            if pdf_text.strip():
                extraction_results.append({
                    "method": "pypdf2",
                    "text": pdf_text,
                    "confidence": 0.7
                })
            
            # Method 2: PyMuPDF for better PDF handling
            pymupdf_text = await self._extract_with_pymupdf(file_path)
            if pymupdf_text.strip():
                extraction_results.append({
                    "method": "pymupdf",
                    "text": pymupdf_text,
                    "confidence": 0.8
                })
            
            # Choose best extraction result
            best_result = self._choose_best_extraction(extraction_results)
            
            return {
                "extracted_text": best_result["text"],
                "extraction_method": best_result["method"],
                "extraction_confidence": best_result["confidence"],
                "all_extractions": extraction_results
            }
            
        except Exception as e:
            logger.error(f"Text extraction failed for {document.get('filename', 'unknown')}: {str(e)}")
            return {
                "extracted_text": "",
                "extraction_method": "failed",
                "extraction_confidence": 0.0,
                "error": str(e)
            }
    
    async def _extract_with_pypdf2(self, file_path: str) -> str:
        """Extract text using PyPDF2"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {str(e)}")
            return ""
    
    async def _extract_with_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF (better for complex PDFs)"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text.strip()
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {str(e)}")
            return ""
    
    def _choose_best_extraction(self, extractions: list) -> Dict[str, Any]:
        """Choose the best extraction result based on confidence and text quality"""
        if not extractions:
            return {
                "method": "none",
                "text": "",
                "confidence": 0.0
            }
        
        # Score extractions based on multiple factors
        scored_extractions = []
        
        for extraction in extractions:
            text = extraction["text"]
            base_confidence = extraction["confidence"]
            
            # Quality scoring factors
            length_score = min(len(text) / 1000, 1.0)  # Longer text usually better
            word_count = len(text.split())
            word_score = min(word_count / 100, 1.0)
            
            # Check for medical keywords (indicates successful extraction)
            medical_keywords = [
                "patient", "doctor", "hospital", "diagnosis", "treatment",
                "date", "amount", "$", "insurance", "claim"
            ]
            keyword_matches = sum(1 for keyword in medical_keywords if keyword.lower() in text.lower())
            keyword_score = min(keyword_matches / len(medical_keywords), 1.0)
            
            # Combined score
            quality_score = (length_score + word_score + keyword_score) / 3
            final_score = (base_confidence + quality_score) / 2
            
            scored_extractions.append({
                **extraction,
                "final_score": final_score
            })
        
        # Return best extraction
        best = max(scored_extractions, key=lambda x: x["final_score"])
        return {
            "method": best["method"],
            "text": best["text"],
            "confidence": best["final_score"]
        }
