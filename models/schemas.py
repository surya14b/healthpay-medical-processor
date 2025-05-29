"""
Pydantic models for HealthPay claim processing
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime, date

class DocumentType(str, Enum):
    BILL = "bill"
    DISCHARGE_SUMMARY = "discharge_summary"
    ID_CARD = "id_card"
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    UNKNOWN = "unknown"

class ClaimStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"

class ProcessedDocument(BaseModel):
    type: DocumentType
    filename: str
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_data: Dict[str, Any]
    
    # Common fields that might be present
    hospital_name: Optional[str] = None
    patient_name: Optional[str] = None
    total_amount: Optional[float] = None
    date_of_service: Optional[Union[str, date]] = None
    admission_date: Optional[Union[str, date]] = None
    discharge_date: Optional[Union[str, date]] = None
    diagnosis: Optional[str] = None
    doctor_name: Optional[str] = None
    treatment_details: Optional[str] = None
    registration_no: Optional[str] = None
    episode_no: Optional[str] = None

class ValidationResult(BaseModel):
    missing_documents: List[str] = []
    discrepancies: List[str] = []
    warnings: List[str] = []
    data_quality_score: float = Field(ge=0.0, le=1.0, default=0.0)

class ClaimDecision(BaseModel):
    status: ClaimStatus
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk_factors: List[str] = []
    recommended_actions: List[str] = []

class ClaimProcessingResponse(BaseModel):
    """Main response model for claim processing"""
    documents: List[ProcessedDocument]
    validation: ValidationResult
    claim_decision: ClaimDecision
    processing_metadata: Dict[str, Any] = {
        "processed_at": datetime.now().isoformat(),
        "processing_time_ms": 0,
        "agent_version": "1.0.0-multi-agent"
    }

class AgentResponse(BaseModel):
    """Generic agent response model"""
    success: bool
    data: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    processing_time: float
    errors: List[str] = []
