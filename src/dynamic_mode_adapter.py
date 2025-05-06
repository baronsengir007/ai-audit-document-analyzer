"""
Dynamic Mode Adapter Module
Handles dynamic policy-based document processing.
"""

import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import json
import logging

from interfaces import (
    Document,
    ValidationResult,
    DocumentProcessor,
    ValidationStrategy,
    ValidationMode,
    ComplianceResult
)
from document_processor import (
    extract_text_from_pdf,
    extract_text_from_word,
    extract_text_from_excel
)
from document_classifier import classify_document
from compliance_evaluator import ComplianceEvaluator, ComplianceLevel
from requirement_store import RequirementStore
from output_format import (
    ValidationStatus,
    ValidationMetadata,
    ValidationItem,
    ValidationCategory,
    ValidationResultFormatter
)

class DynamicDocumentProcessor(DocumentProcessor):
    """Adapter for dynamic mode document processing"""
    def process_document(self, doc_path: Path) -> Document:
        # Extract text based on file type
        if doc_path.suffix.lower() == '.pdf':
            content = extract_text_from_pdf(str(doc_path))
        elif doc_path.suffix.lower() == '.docx':
            content = extract_text_from_word(str(doc_path))
        elif doc_path.suffix.lower() == '.xlsx':
            content = extract_text_from_excel(str(doc_path))
        else:
            raise ValueError(f"Unsupported file type: {doc_path.suffix}")

        # Create document object
        doc = {
            "filename": doc_path.name,
            "type": doc_path.suffix.lower()[1:],
            "content": content
        }

        # Classify document
        classification = classify_document(doc)

        return Document(
            filename=doc_path.name,
            content=content,
            classification=classification,
            metadata={"file_type": doc_path.suffix.lower()[1:]},
            source_path=doc_path
        )

class DynamicValidationStrategy:
    """Adapter for dynamic mode validation strategy"""
    def __init__(self, requirement_store: RequirementStore, llm_config: Optional[Dict[str, Any]] = None):
        self.requirement_store = requirement_store
        self.llm_config = llm_config or {}
        self.logger = logging.getLogger(__name__)
        self.evaluator = ComplianceEvaluator(
            requirement_store=requirement_store,
            llm_wrapper=None,  # Will be initialized on first use if needed
            config=self.llm_config
        )

    def validate(self, document: Document) -> ValidationResult:
        try:
            # Process document with compliance evaluator
            doc_dict = {
                "filename": document.filename,
                "content": document.content,
                "type": document.classification
            }
            
            # Evaluate compliance
            evaluation_result = self.evaluator.evaluate_document_compliance(doc_dict)
            
            # Map compliance levels to validation status
            status_mapping = {
                ComplianceLevel.FULLY_COMPLIANT: ValidationStatus.PASSED,
                ComplianceLevel.PARTIALLY_COMPLIANT: ValidationStatus.WARNING,
                ComplianceLevel.NON_COMPLIANT: ValidationStatus.FAILED,
                ComplianceLevel.NOT_APPLICABLE: ValidationStatus.SKIPPED,
                ComplianceLevel.INDETERMINATE: ValidationStatus.UNKNOWN
            }
            
            # Create validation items for each requirement
            items = []
            for req_id, req_result in evaluation_result.requirement_results.items():
                items.append(
                    ValidationItem(
                        id=req_id,
                        name=req_result.requirement.description,
                        status=status_mapping.get(req_result.compliance_level, ValidationStatus.UNKNOWN),
                        confidence_score=req_result.confidence_score,
                        errors=[] if req_result.compliance_level != ComplianceLevel.NON_COMPLIANT else 
                               [req_result.justification]
                    )
                )
            
            # Create categories based on requirement types
            categories = {}
            for req_id, req_result in evaluation_result.requirement_results.items():
                category_id = req_result.requirement.type.value
                if category_id not in categories:
                    categories[category_id] = {
                        "id": category_id,
                        "name": req_result.requirement.type.value.title(),
                        "items": [],
                        "passed": 0,
                        "failed": 0,
                        "warning": 0,
                        "unknown": 0
                    }
                
                categories[category_id]["items"].append(req_id)
                
                status = status_mapping.get(req_result.compliance_level, ValidationStatus.UNKNOWN)
                if status == ValidationStatus.PASSED:
                    categories[category_id]["passed"] += 1
                elif status == ValidationStatus.FAILED:
                    categories[category_id]["failed"] += 1
                elif status == ValidationStatus.WARNING:
                    categories[category_id]["warning"] += 1
                else:
                    categories[category_id]["unknown"] += 1
            
            # Convert categories to ValidationCategory objects
            validation_categories = []
            for cat_id, cat_data in categories.items():
                # Determine category status based on item results
                if cat_data["failed"] > 0:
                    cat_status = ValidationStatus.FAILED
                elif cat_data["warning"] > 0:
                    cat_status = ValidationStatus.WARNING
                elif cat_data["passed"] > 0:
                    cat_status = ValidationStatus.PASSED
                else:
                    cat_status = ValidationStatus.UNKNOWN
                
                # Get all items for this category
                cat_items = [item for item in items if item.id in cat_data["items"]]
                
                validation_categories.append(
                    ValidationCategory(
                        id=cat_id,
                        name=cat_data["name"],
                        status=cat_status,
                        confidence_score=evaluation_result.overall_confidence,
                        items=cat_items
                    )
                )
            
            # Determine overall status
            overall_status = ValidationStatus.PASSED
            if any(cat.status == ValidationStatus.FAILED for cat in validation_categories):
                overall_status = ValidationStatus.FAILED
            elif any(cat.status == ValidationStatus.WARNING for cat in validation_categories):
                overall_status = ValidationStatus.WARNING
            elif all(cat.status == ValidationStatus.UNKNOWN for cat in validation_categories):
                overall_status = ValidationStatus.UNKNOWN
            
            return ValidationResult(
                document_id=document.filename,
                document_name=document.filename,
                document_type=document.classification,
                status=overall_status,
                metadata=ValidationMetadata(
                    mode="dynamic",
                    processing_time=evaluation_result.processing_time
                ),
                categories=validation_categories
            )

        except Exception as e:
            self.logger.error(f"Error in dynamic validation: {str(e)}")
            return ValidationResult(
                document_id=document.filename,
                document_name=document.filename,
                document_type=document.classification,
                status=ValidationStatus.ERROR,
                metadata=ValidationMetadata(
                    mode="dynamic",
                    warnings=[str(e)]
                ),
                errors=[str(e)]
            )

class DynamicValidationMode(ValidationMode):
    """Adapter for dynamic mode validation"""
    def __init__(self):
        self.processor = DynamicDocumentProcessor()
        self.strategy = None
        self.config = None

    def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.strategy = DynamicValidationStrategy(
            requirement_store=config.get("requirement_store"),
            llm_config=config.get("llm_config")
        )

    def process_batch(self, documents: List[Document]) -> List[ValidationResult]:
        results = []
        with ThreadPoolExecutor(max_workers=self.config.get("max_workers", 4)) as executor:
            futures = [executor.submit(self.strategy.validate, doc) for doc in documents]
            for future in futures:
                results.append(future.result())
        return results

    def save_results(self, results: List[ValidationResult], output_path: Path) -> None:
        # Save each result individually
        for result in results:
            result_path = output_path.parent / f"{result.document_id}_dynamic_validation.json"
            ValidationResultFormatter.save_to_file(result, result_path)
        
        # Save summary
        summary = {
            "total_documents": len(results),
            "passed_documents": sum(1 for r in results if r.status == ValidationStatus.PASSED),
            "failed_documents": sum(1 for r in results if r.status == ValidationStatus.FAILED),
            "warning_documents": sum(1 for r in results if r.status == ValidationStatus.WARNING),
            "unknown_documents": sum(1 for r in results if r.status == ValidationStatus.UNKNOWN),
            "error_documents": sum(1 for r in results if r.status == ValidationStatus.ERROR)
        }
        
        summary_path = output_path.parent / "dynamic_validation_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

class DynamicModeAdapter:
    """Handles dynamic mode document processing."""
    
    def __init__(self, requirement_store: Optional[RequirementStore] = None, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.requirement_store = requirement_store
        self.config = config or {}
        self.evaluator = None
    
    def process(self, document: Document) -> ComplianceResult:
        """Process a document in dynamic mode"""
        try:
            # Initialize evaluator if needed
            if not self.evaluator:
                self.evaluator = ComplianceEvaluator(
                    requirement_store=self.requirement_store,
                    llm_wrapper=None,  # Will be initialized on first use if needed
                    config=self.config
                )
            
            # Convert Document to dictionary format expected by evaluator
            doc_dict = {
                "filename": document.filename,
                "content": document.content,
                "type": document.classification
            }
            
            # Evaluate compliance
            evaluation_result = self.evaluator.evaluate_document_compliance(doc_dict)
            
            # Map evaluation result to ComplianceResult
            is_compliant = evaluation_result.overall_compliance in [
                ComplianceLevel.FULLY_COMPLIANT, 
                ComplianceLevel.PARTIALLY_COMPLIANT
            ]
            
            return ComplianceResult(
                is_compliant=is_compliant,
                confidence=evaluation_result.overall_confidence,
                details={
                    "overall_compliance": evaluation_result.overall_compliance.value,
                    "requirement_results": {
                        req_id: {
                            "compliance_level": req_result.compliance_level.value,
                            "confidence_score": req_result.confidence_score,
                            "justification": req_result.justification
                        } for req_id, req_result in evaluation_result.requirement_results.items()
                    },
                    "processing_time": evaluation_result.processing_time
                },
                mode_used="dynamic"
            )
            
        except Exception as e:
            self.logger.error(f"Error in dynamic processing: {str(e)}")
            return ComplianceResult(
                is_compliant=False,
                confidence=0.0,
                details={"error": str(e)},
                mode_used="dynamic_error"
            )