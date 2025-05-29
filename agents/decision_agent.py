import asyncio
from typing import Dict, Any, List
import logging
from models.schemas import ProcessedDocument, ValidationResult, ClaimDecision, ClaimStatus

logger = logging.getLogger(__name__)

class DecisionAgent:
    def __init__(self):
        self.approval_threshold = 0.7
        self.rejection_threshold = 0.3
    
    async def make_decision(self, documents: List[ProcessedDocument], 
                          validation: ValidationResult) -> ClaimDecision:
        """Make final claim decision based on processed data and validation"""
        try:
            # Calculate decision score
            decision_score = self._calculate_decision_score(documents, validation)
            
            # Determine status
            if decision_score >= self.approval_threshold:
                status = ClaimStatus.APPROVED
                reason = self._generate_approval_reason(documents, validation, decision_score)
            elif decision_score <= self.rejection_threshold:
                status = ClaimStatus.REJECTED
                reason = self._generate_rejection_reason(documents, validation, decision_score)
            else:
                status = ClaimStatus.PENDING
                reason = "Requires manual review - mixed confidence indicators"
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(documents, validation)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(status, risk_factors, validation)
            
            return ClaimDecision(
                status=status,
                reason=reason,
                confidence=decision_score,
                risk_factors=risk_factors,
                recommended_actions=recommendations
            )
            
        except Exception as e:
            logger.error(f"Decision making failed: {str(e)}")
            return ClaimDecision(
                status=ClaimStatus.REJECTED,
                reason=f"Decision process failed: {str(e)}",
                confidence=0.0,
                risk_factors=["system_error"]
            )
    
    def _calculate_decision_score(self, documents: List[ProcessedDocument], 
                                validation: ValidationResult) -> float:
        """Calculate decision confidence score"""
        score_components = []
        
        # Data quality score (40% weight)
        score_components.append(validation.data_quality_score * 0.4)
        
        # Document completeness (30% weight)
        completeness_score = 1.0 - (len(validation.missing_documents) * 0.3)
        completeness_score = max(0.0, completeness_score)
        score_components.append(completeness_score * 0.3)
        
        # Data consistency (20% weight)
        consistency_score = 1.0 - (len(validation.discrepancies) * 0.2)
        consistency_score = max(0.0, consistency_score)
        score_components.append(consistency_score * 0.2)
        
        # Document confidence average (10% weight)
        if documents:
            avg_confidence = sum(doc.confidence for doc in documents) / len(documents)
            score_components.append(avg_confidence * 0.1)
        
        return sum(score_components)
    
    def _generate_approval_reason(self, documents: List[ProcessedDocument], 
                                validation: ValidationResult, score: float) -> str:
        """Generate approval reason"""
        reasons = []
        
        if not validation.missing_documents:
            reasons.append("All required documents present")
        
        if not validation.discrepancies:
            reasons.append("Data is consistent across documents")
        
        if validation.data_quality_score > 0.8:
            reasons.append("High data quality score")
        
        if not reasons:
            reasons.append(f"Overall confidence score: {score:.2f}")
        
        return "; ".join(reasons)
    
    def _generate_rejection_reason(self, documents: List[ProcessedDocument], 
                                 validation: ValidationResult, score: float) -> str:
        """Generate rejection reason"""
        reasons = []
        
        if validation.missing_documents:
            reasons.append(f"Missing required documents: {', '.join(validation.missing_documents)}")
        
        if validation.discrepancies:
            reasons.append(f"Data discrepancies: {len(validation.discrepancies)} issues")
        
        if validation.data_quality_score < 0.3:
            reasons.append("Poor data quality")
        
        if not reasons:
            reasons.append(f"Low confidence score: {score:.2f}")
        
        return "; ".join(reasons)
    
    def _identify_risk_factors(self, documents: List[ProcessedDocument], 
                             validation: ValidationResult) -> List[str]:
        """Identify risk factors"""
        risks = []
        
        if validation.missing_documents:
            risks.append("incomplete_documentation")
        
        if validation.discrepancies:
            risks.append("data_inconsistency")
        
        if validation.data_quality_score < 0.5:
            risks.append("low_data_quality")
        
        # Check for high amounts
        for doc in documents:
            if doc.type == "bill":
                amount = getattr(doc, 'total_amount', 0)
                if amount and amount > 500000:  # ₹5L threshold
                    risks.append("high_claim_amount")
        
        return risks
    
    def _generate_recommendations(self, status: ClaimStatus, risk_factors: List[str], 
                                validation: ValidationResult) -> List[str]:
        """Generate recommended actions"""
        recommendations = []
        
        if status == ClaimStatus.PENDING:
            recommendations.append("Manual review required")
        
        if "incomplete_documentation" in risk_factors:
            recommendations.append("Request missing documents")
        
        if "data_inconsistency" in risk_factors:
            recommendations.append("Verify data discrepancies")
        
        if "high_claim_amount" in risk_factors:
            recommendations.append("Secondary review for high-value claim")
        
        if validation.warnings:
            recommendations.append("Address data quality warnings")
        
        return recommendations
