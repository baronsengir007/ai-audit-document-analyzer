"""
Edge Case Handler Module
Handles various edge cases that may occur during document analysis.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from pathlib import Path
import json

class EdgeCaseType(Enum):
    """Types of edge cases that can occur"""
    LLM_EXTRACTION_FAILURE = "llm_extraction_failure"
    UNMATCHED_DOCUMENT = "unmatched_document"
    AMBIGUOUS_COMPLIANCE = "ambiguous_compliance"
    CORRUPTED_EVALUATION = "corrupted_evaluation"
    UNEXPECTED_INPUT = "unexpected_input"
    TIMEOUT = "timeout"
    LOW_QUALITY_RESPONSE = "low_quality_response"

class EdgeCaseHandler:
    """Handles edge cases in document analysis"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.stats = {case_type: 0 for case_type in EdgeCaseType}
        self.log_dir = log_dir or Path("logs/edge_cases")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Add file handler for edge case logs
        log_file = self.log_dir / "edge_cases.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)
    
    def handle_edge_case(self, 
                        case_type: EdgeCaseType, 
                        document_id: str,
                        details: Dict[str, Any],
                        recovery_strategy: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle an edge case and log it
        
        Args:
            case_type: Type of edge case
            document_id: ID of the document that caused the edge case
            details: Additional details about the edge case
            recovery_strategy: Optional recovery strategy to apply
            
        Returns:
            Dict containing handling results
        """
        # Update statistics
        self.stats[case_type] += 1
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "case_type": case_type.value,
            "document_id": document_id,
            "details": details,
            "recovery_strategy": recovery_strategy
        }
        
        # Log the edge case
        self.logger.info(f"Edge case detected: {case_type.value} for document {document_id}")
        if recovery_strategy:
            self.logger.info(f"Applying recovery strategy: {recovery_strategy}")
        
        # Save detailed log
        log_file = self.log_dir / f"{document_id}_{case_type.value}.json"
        with open(log_file, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        # Apply recovery strategy if specified
        result = {"handled": True, "case_type": case_type.value}
        if recovery_strategy:
            result.update(self._apply_recovery_strategy(recovery_strategy, document_id, details))
        
        return result
    
    def _apply_recovery_strategy(self, 
                               strategy: str, 
                               document_id: str,
                               details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a recovery strategy for an edge case
        
        Args:
            strategy: Name of the recovery strategy
            document_id: ID of the document
            details: Details about the edge case
            
        Returns:
            Dict containing recovery results
        """
        strategies = {
            "retry": self._retry_processing,
            "fallback": self._fallback_processing,
            "skip": self._skip_processing,
            "manual_review": self._flag_for_manual_review
        }
        
        if strategy in strategies:
            return strategies[strategy](document_id, details)
        else:
            self.logger.warning(f"Unknown recovery strategy: {strategy}")
            return {"recovery_status": "unknown_strategy"}
    
    def _retry_processing(self, document_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Retry processing the document"""
        self.logger.info(f"Retrying processing for document {document_id}")
        return {"recovery_status": "retry_attempted"}
    
    def _fallback_processing(self, document_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Use fallback processing method"""
        self.logger.info(f"Using fallback processing for document {document_id}")
        return {"recovery_status": "fallback_used"}
    
    def _skip_processing(self, document_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Skip processing the document"""
        self.logger.info(f"Skipping processing for document {document_id}")
        return {"recovery_status": "skipped"}
    
    def _flag_for_manual_review(self, document_id: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Flag document for manual review"""
        self.logger.info(f"Flagging document {document_id} for manual review")
        return {"recovery_status": "manual_review_required"}
    
    def get_edge_case_stats(self) -> Dict[str, Any]:
        """Get statistics about edge case occurrences"""
        return {
            "total_cases": sum(self.stats.values()),
            "by_type": {case_type.value: count for case_type, count in self.stats.items()}
        }
    
    def get_recent_edge_cases(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent edge cases
        
        Args:
            limit: Maximum number of cases to return
            
        Returns:
            List of recent edge cases
        """
        cases = []
        for log_file in sorted(self.log_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            if len(cases) >= limit:
                break
            with open(log_file) as f:
                cases.append(json.load(f))
        return cases