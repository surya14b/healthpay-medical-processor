"""
Main orchestrator for managing the multi-agent workflow
"""

import asyncio
import time
from typing import List, Dict, Any
from fastapi import UploadFile
import logging

from agents.classifier_agent import DocumentClassifierAgent
from agents.extraction_agent import TextExtractionAgent
from agents.bill_agent import BillProcessingAgent
from agents.discharge_agent import DischargeProcessingAgent
from agents.validation_agent import ValidationAgent
from agents.decision_agent import DecisionAgent
from models.schemas import (
    ClaimProcessingResponse, ProcessedDocument, ValidationResult,
    ClaimDecision, DocumentType
)
from utils.file_handler import FileHandler

logger = logging.getLogger(__name__)

class ClaimProcessingOrchestrator:
    """
    Orchestrates the multi-agent workflow for processing medical claim documents
    """
    
    def __init__(self):
        self.file_handler = FileHandler()
        
        # Initialize agents
        self.classifier_agent = DocumentClassifierAgent()
        self.extraction_agent = TextExtractionAgent()
        self.bill_agent = BillProcessingAgent()
        self.discharge_agent = DischargeProcessingAgent()
        self.validation_agent = ValidationAgent()
        self.decision_agent = DecisionAgent()
        
        logger.info("ClaimProcessingOrchestrator initialized with 6 agents")
    
    async def process_claim_documents(self, files: List[UploadFile]) -> ClaimProcessingResponse:
        """
        Main orchestration method that processes claim documents through the agent pipeline
        """
        start_time = time.time()
        
        try:
            logger.info("🚀 Starting multi-agent claim processing pipeline...")
            
            # Step 1: Save and validate uploaded files
            logger.info("📁 Step 1: Saving uploaded files...")
            saved_files = await self._save_uploaded_files(files)
            
            # Step 2: Classify documents
            logger.info("🔍 Step 2: Classifying documents...")
            classified_docs = await self._classify_documents(saved_files)
            
            # Step 3: Extract text from all documents
            logger.info("📝 Step 3: Extracting text...")
            extracted_texts = await self._extract_texts(classified_docs)
            
            # Step 4: Process documents with specialized agents
            logger.info("🤖 Step 4: Processing with specialized agents...")
            processed_docs = await self._process_with_specialized_agents(extracted_texts)
            
            # Step 5: Validate processed data
            logger.info("✅ Step 5: Validating processed data...")
            validation_result = await self._validate_processed_data(processed_docs)
            
            # Step 6: Make final claim decision
            logger.info("🎯 Step 6: Making final claim decision...")
            claim_decision = await self._make_claim_decision(processed_docs, validation_result)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            logger.info(f"🏁 Multi-agent processing completed in {processing_time:.0f}ms")
            
            return ClaimProcessingResponse(
                documents=processed_docs,
                validation=validation_result,
                claim_decision=claim_decision,
                processing_metadata={
                    "processed_at": time.time(),
                    "processing_time_ms": processing_time,
                    "agent_version": "1.0.0-multi-agent",
                    "files_processed": len(files),
                    "agents_used": [
                        "DocumentClassifierAgent",
                        "TextExtractionAgent", 
                        "BillProcessingAgent" if any(doc.type == "bill" for doc in processed_docs) else None,
                        "DischargeProcessingAgent" if any(doc.type == "discharge_summary" for doc in processed_docs) else None,
                        "ValidationAgent",
                        "DecisionAgent"
                    ]
                }
            )
            
        except Exception as e:
            logger.error(f"💥 Error in claim processing orchestration: {str(e)}")
            raise
    
    async def _save_uploaded_files(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
        """Save uploaded files and return file metadata"""
        saved_files = []
        
        for file in files:
            try:
                file_info = await self.file_handler.save_uploaded_file(file)
                saved_files.append(file_info)
                logger.info(f"✅ Saved file: {file.filename}")
            except Exception as e:
                logger.error(f"❌ Error saving file {file.filename}: {str(e)}")
                # Continue processing other files
                
        return saved_files
    
    async def _classify_documents(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify documents using the classifier agent"""
        classified_docs = []
        
        # Process classifications concurrently
        classification_tasks = [
            self.classifier_agent.classify_document(file_info)
            for file_info in files
        ]
        
        classification_results = await asyncio.gather(*classification_tasks, return_exceptions=True)
        
        for i, result in enumerate(classification_results):
            if isinstance(result, Exception):
                logger.error(f"❌ Classification error for {files[i]['filename']}: {str(result)}")
                # Assign unknown type for failed classifications
                files[i]['document_type'] = DocumentType.UNKNOWN
                files[i]['classification_confidence'] = 0.0
            else:
                files[i].update(result)
                logger.info(f"🔍 Classified {files[i]['filename']} as {result.get('document_type')}")
            
            classified_docs.append(files[i])
        
        return classified_docs
    
    async def _extract_texts(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract text from documents using the extraction agent"""
        extraction_tasks = [
            self.extraction_agent.extract_text(doc)
            for doc in documents
        ]
        
        extraction_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        
        for i, result in enumerate(extraction_results):
            if isinstance(result, Exception):
                logger.error(f"❌ Text extraction error for {documents[i]['filename']}: {str(result)}")
                documents[i]['extracted_text'] = ""
                documents[i]['extraction_confidence'] = 0.0
            else:
                documents[i].update(result)
                logger.info(f"📝 Extracted {len(result.get('extracted_text', ''))} chars from {documents[i]['filename']}")
        
        return documents
    
    async def _process_with_specialized_agents(self, documents: List[Dict[str, Any]]) -> List[ProcessedDocument]:
        """Process documents with specialized agents based on document type"""
        processed_docs = []
        
        for doc in documents:
            doc_type = doc.get('document_type', DocumentType.UNKNOWN)
            
            try:
                if doc_type == DocumentType.BILL:
                    logger.info(f"💰 Processing {doc['filename']} with BillProcessingAgent")
                    result = await self.bill_agent.process_bill(doc)
                elif doc_type == DocumentType.DISCHARGE_SUMMARY:
                    logger.info(f"🏥 Processing {doc['filename']} with DischargeProcessingAgent")
                    result = await self.discharge_agent.process_discharge_summary(doc)
                else:
                    logger.info(f"📄 Processing {doc['filename']} with generic processing")
                    result = await self._process_generic_document(doc)
                
                # Extract confidence and structured data safely
                confidence = result.get('confidence', 0.5)
                structured_data = result.get('structured_data', {})
                
                # Remove confidence from structured_data to avoid conflict
                structured_data_clean = {k: v for k, v in structured_data.items() if k != 'confidence'}
                
                # Create ProcessedDocument with explicit field mapping
                processed_doc = ProcessedDocument(
                    type=doc_type,
                    filename=doc['filename'],
                    confidence=confidence,
                    extracted_data=structured_data_clean,
                    # Map specific fields from structured_data
                    hospital_name=structured_data_clean.get('hospital_name'),
                    patient_name=structured_data_clean.get('patient_name'),
                    total_amount=structured_data_clean.get('total_amount'),
                    date_of_service=structured_data_clean.get('date_of_service'),
                    admission_date=structured_data_clean.get('admission_date'),
                    discharge_date=structured_data_clean.get('discharge_date'),
                    diagnosis=structured_data_clean.get('diagnosis'),
                    doctor_name=structured_data_clean.get('doctor_name'),
                    treatment_details=structured_data_clean.get('treatment_details'),
                    registration_no=structured_data_clean.get('registration_no'),
                    episode_no=structured_data_clean.get('episode_no')
                )
                
                processed_docs.append(processed_doc)
                logger.info(f"✅ Processed {doc['filename']} with confidence {confidence:.2f}")
                
            except Exception as e:
                logger.error(f"❌ Error processing {doc['filename']} with specialized agent: {str(e)}")
                # Create a basic processed document for failed processing
                processed_doc = ProcessedDocument(
                    type=doc_type,
                    filename=doc['filename'],
                    confidence=0.0,
                    extracted_data={"error": str(e)}
                )
                processed_docs.append(processed_doc)
        
        return processed_docs
    
    async def _process_generic_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Generic document processing for unknown document types"""
        return {
            "confidence": 0.3,
            "structured_data": {
                "raw_text": doc.get('extracted_text', ''),
                "processing_note": "Generic processing applied"
            }
        }
    
    async def _validate_processed_data(self, documents: List[ProcessedDocument]) -> ValidationResult:
        """Validate processed documents for consistency and completeness"""
        try:
            return await self.validation_agent.validate_claim_data(documents)
        except Exception as e:
            logger.error(f"❌ Error in validation: {str(e)}")
            return ValidationResult(
                missing_documents=["validation_failed"],
                discrepancies=[f"Validation error: {str(e)}"],
                data_quality_score=0.0
            )
    
    async def _make_claim_decision(self, documents: List[ProcessedDocument], 
                                 validation: ValidationResult) -> ClaimDecision:
        """Make final claim decision based on processed data and validation"""
        try:
            return await self.decision_agent.make_decision(documents, validation)
        except Exception as e:
            logger.error(f"❌ Error in decision making: {str(e)}")
            return ClaimDecision(
                status="rejected",
                reason=f"Decision making failed: {str(e)}",
                confidence=0.0,
                risk_factors=["system_error"]
            )
