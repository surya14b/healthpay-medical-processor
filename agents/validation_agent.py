import asyncio
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
from models.schemas import ProcessedDocument, ValidationResult

logger = logging.getLogger(__name__)

class ValidationAgent:
    def __init__(self):
        self.required_documents = ["bill", "discharge_summary"]
        self.optional_documents = ["id_card", "prescription", "lab_report"]
    
    async def validate_claim_data(self, documents: List[ProcessedDocument]) -> ValidationResult:
        """Validate processed documents for consistency and completeness"""
        try:
            missing_docs = self._check_missing_documents(documents)
            discrepancies = await self._check_data_discrepancies(documents)
            warnings = self._generate_warnings(documents)
            quality_score = self._calculate_data_quality_score(documents)
            
            return ValidationResult(
                missing_documents=missing_docs,
                discrepancies=discrepancies,
                warnings=warnings,
                data_quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return ValidationResult(
                missing_documents=["validation_error"],
                discrepancies=[f"Validation failed: {str(e)}"],
                data_quality_score=0.0
            )
    
    def _check_missing_documents(self, documents: List[ProcessedDocument]) -> List[str]:
        """Check for missing required documents"""
        missing = []
        present_types = {doc.type for doc in documents}
        
        for required_type in self.required_documents:
            if required_type not in present_types:
                missing.append(required_type)
        
        return missing
    
    async def _check_data_discrepancies(self, documents: List[ProcessedDocument]) -> List[str]:
        """Check for data inconsistencies between documents"""
        discrepancies = []
        
        # Get bill and discharge summary
        bill_doc = next((doc for doc in documents if doc.type == "bill"), None)
        discharge_doc = next((doc for doc in documents if doc.type == "discharge_summary"), None)
        
        if bill_doc and discharge_doc:
            # Check patient name consistency
            bill_patient = getattr(bill_doc, 'patient_name', None)
            discharge_patient = getattr(discharge_doc, 'patient_name', None)
            
            if bill_patient and discharge_patient:
                if not self._names_match(bill_patient, discharge_patient):
                    discrepancies.append(f"Patient name mismatch: Bill({bill_patient}) vs Discharge({discharge_patient})")
            
            # Check hospital name consistency
            bill_hospital = getattr(bill_doc, 'hospital_name', None)
            discharge_hospital = getattr(discharge_doc, 'hospital_name', None)
            
            if bill_hospital and discharge_hospital:
                if not self._hospitals_match(bill_hospital, discharge_hospital):
                    discrepancies.append(f"Hospital mismatch: {bill_hospital} vs {discharge_hospital}")
            
            # Check date consistency
            bill_service_date = getattr(bill_doc, 'date_of_service', None)
            discharge_date = getattr(discharge_doc, 'discharge_date', None)
            admission_date = getattr(discharge_doc, 'admission_date', None)
            
            if bill_service_date and admission_date and discharge_date:
                date_issue = self._check_date_consistency(bill_service_date, admission_date, discharge_date)
                if date_issue:
                    discrepancies.append(date_issue)
        
        return discrepancies
    
    def _names_match(self, name1: str, name2: str) -> bool:
        """Check if patient names match"""
        if not name1 or not name2:
            return False
        
        # Normalize names
        name1_clean = ''.join(name1.lower().split())
        name2_clean = ''.join(name2.lower().split())
        
        # Check similarity
        return (name1_clean in name2_clean or name2_clean in name1_clean or 
                len(set(name1.lower().split()) & set(name2.lower().split())) >= 1)
    
    def _hospitals_match(self, hospital1: str, hospital2: str) -> bool:
        """Check if hospital names match"""
        if not hospital1 or not hospital2:
            return False
        
        h1_words = set(hospital1.lower().split())
        h2_words = set(hospital2.lower().split())
        
        # Remove common words
        ignore_words = {'hospital', 'medical', 'center', 'clinic', 'the', 'of', 'and'}
        h1_words -= ignore_words
        h2_words -= ignore_words
        
        return len(h1_words & h2_words) > 0
    
    def _check_date_consistency(self, service_date: str, admission_date: str, discharge_date: str) -> str:
        """Check date logical consistency"""
        try:
            # Basic date consistency check
            if service_date and admission_date:
                # Service date should be within admission period
                return ""  # Simplified for now
            return ""
        except Exception:
            return "Date validation failed"
    
    def _generate_warnings(self, documents: List[ProcessedDocument]) -> List[str]:
        """Generate warnings based on document quality"""
        warnings = []
        
        # Check confidence levels
        low_confidence_docs = [doc for doc in documents if doc.confidence < 0.5]
        if low_confidence_docs:
            warnings.append(f"{len(low_confidence_docs)} documents have low confidence")
        
        # Check for missing critical data
        for doc in documents:
            if doc.type == "bill":
                if not getattr(doc, 'total_amount', None):
                    warnings.append("Bill amount not found")
                if not getattr(doc, 'hospital_name', None):
                    warnings.append("Hospital name missing from bill")
            
            elif doc.type == "discharge_summary":
                if not getattr(doc, 'diagnosis', None):
                    warnings.append("Diagnosis not found in discharge summary")
        
        return warnings
    
    def _calculate_data_quality_score(self, documents: List[ProcessedDocument]) -> float:
        """Calculate overall data quality score"""
        if not documents:
            return 0.0
        
        total_score = 0.0
        for doc in documents:
            doc_score = doc.confidence
            
            # Bonus for having key fields
            if doc.type == "bill":
                if getattr(doc, 'total_amount', None):
                    doc_score += 0.1
                if getattr(doc, 'hospital_name', None):
                    doc_score += 0.1
                if getattr(doc, 'patient_name', None):
                    doc_score += 0.1
            
            elif doc.type == "discharge_summary":
                if getattr(doc, 'diagnosis', None):
                    doc_score += 0.1
                if getattr(doc, 'admission_date', None):
                    doc_score += 0.1
            
            total_score += min(doc_score, 1.0)
        
        return total_score / len(documents)
