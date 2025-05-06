import time
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import json

from .interfaces import (
    Document,
    ValidationResult,
    DocumentProcessor,
    ValidationStrategy,
    ValidationMode,
    ComplianceResult
)
from .document_processor import (
    extract_text_from_pdf,
    extract_text_from_word,
    extract_text_from_excel
)
from .document_classifier import classify_document
from .checklist_validator import scan_and_report_keywords
from .output_format import (
    ValidationStatus,
    ValidationMetadata,
    ValidationItem,
    ValidationCategory,
    ValidationResultFormatter
)

class StaticDocumentProcessor(DocumentProcessor):
    """Adapter for static mode document processing"""
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

class StaticValidationStrategy:
    """Adapter for static mode validation strategy"""
    def __init__(self, checklist_map: Dict[str, List[str]], type_to_checklist_id: Dict[str, str]):
        self.checklist_map = checklist_map
        self.type_to_checklist_id = type_to_checklist_id

    def validate(self, document: Document) -> ValidationResult:
        try:
            # Validate against checklist
            checklist_id = self.type_to_checklist_id.get(document.classification)
            if not checklist_id:
                return ValidationResult(
                    document_id=document.filename,
                    document_name=document.filename,
                    document_type=document.classification,
                    status=ValidationStatus.UNKNOWN,
                    metadata=ValidationMetadata(
                        mode="static",
                        warnings=["Unknown document type"]
                    )
                )

            # Scan for keywords
            results = scan_and_report_keywords(
                [{"content": document.content, "classification": document.classification}],
                self.checklist_map,
                self.type_to_checklist_id
            )

            if not results:
                return ValidationResult(
                    document_id=document.filename,
                    document_name=document.filename,
                    document_type=document.classification,
                    status=ValidationStatus.UNKNOWN,
                    metadata=ValidationMetadata(
                        mode="static",
                        warnings=["No validation results found"]
                    )
                )

            result = results[0]
            
            # Create validation items
            items = []
            for keyword in result["present_keywords"]:
                items.append(
                    ValidationItem(
                        id=f"keyword_{keyword}",
                        name=keyword,
                        status=ValidationStatus.PASSED,
                        confidence_score=1.0
                    )
                )
            
            for keyword in result["missing_keywords"]:
                items.append(
                    ValidationItem(
                        id=f"keyword_{keyword}",
                        name=keyword,
                        status=ValidationStatus.FAILED,
                        confidence_score=1.0,
                        errors=[f"Required keyword '{keyword}' not found"]
                    )
                )

            # Create category
            category = ValidationCategory(
                id=checklist_id,
                name=checklist_id,
                status=ValidationStatus.PASSED if not result["missing_keywords"] else ValidationStatus.FAILED,
                confidence_score=1.0,
                items=items
            )

            # Determine overall status
            status = ValidationStatus.PASSED if not result["missing_keywords"] else ValidationStatus.FAILED

            return ValidationResult(
                document_id=document.filename,
                document_name=document.filename,
                document_type=document.classification,
                status=status,
                metadata=ValidationMetadata(mode="static"),
                categories=[category]
            )

        except Exception as e:
            return ValidationResult(
                document_id=document.filename,
                document_name=document.filename,
                document_type=document.classification,
                status=ValidationStatus.ERROR,
                metadata=ValidationMetadata(
                    mode="static",
                    warnings=[str(e)]
                ),
                errors=[str(e)]
            )

    def get_checklist(self) -> Dict[str, Any]:
        return {
            "checklist_map": self.checklist_map,
            "type_to_checklist_id": self.type_to_checklist_id
        }

class StaticValidationMode(ValidationMode):
    """Adapter for static mode validation"""
    def __init__(self):
        self.processor = StaticDocumentProcessor()
        self.strategy = None
        self.config = None

    def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.strategy = StaticValidationStrategy(
            checklist_map=config["checklist_map"],
            type_to_checklist_id=config["type_to_checklist_id"]
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
            result_path = output_path.parent / f"{result.document_id}_validation.json"
            ValidationResultFormatter.save_to_file(result, result_path)
        
        # Save summary
        summary = {
            "total_documents": len(results),
            "passed_documents": sum(1 for r in results if r.status == ValidationStatus.PASSED),
            "failed_documents": sum(1 for r in results if r.status == ValidationStatus.FAILED),
            "unknown_documents": sum(1 for r in results if r.status == ValidationStatus.UNKNOWN),
            "error_documents": sum(1 for r in results if r.status == ValidationStatus.ERROR)
        }
        
        summary_path = output_path.parent / "validation_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

class StaticModeAdapter:
    """Handles static mode document processing."""
    
    def process(self, document: Document) -> ComplianceResult:
        """Process a document in static mode"""
        return ComplianceResult(
            is_compliant=False,
            confidence=0.0,
            details={},
            mode_used="static"
        ) 