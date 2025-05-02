import time
from pathlib import Path
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

from interfaces import (
    Document,
    ValidationResult,
    DocumentProcessor,
    ValidationStrategy,
    ValidationMode
)
from document_processor import (
    extract_text_from_pdf,
    extract_text_from_word,
    extract_text_from_excel
)
from document_classifier import classify_document
from checklist_validator import scan_and_report_keywords

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

class StaticValidationStrategy(ValidationStrategy):
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
                    document=document,
                    status="unknown_type",
                    validation_results={},
                    mode="static",
                    timestamp=time.time()
                )

            # Scan for keywords
            results = scan_and_report_keywords(
                [{"content": document.content, "classification": document.classification}],
                self.checklist_map,
                self.type_to_checklist_id
            )

            if not results:
                return ValidationResult(
                    document=document,
                    status="unknown_type",
                    validation_results={},
                    mode="static",
                    timestamp=time.time()
                )

            result = results[0]
            status = "complete" if not result["missing_keywords"] else "incomplete"

            return ValidationResult(
                document=document,
                status=status,
                validation_results={
                    "present_keywords": result["present_keywords"],
                    "missing_keywords": result["missing_keywords"]
                },
                mode="static",
                timestamp=time.time()
            )

        except Exception as e:
            return ValidationResult(
                document=document,
                status="error",
                validation_results={},
                mode="static",
                timestamp=time.time(),
                error=str(e)
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
        from interfaces import ValidationResultSerializer
        serialized_results = [ValidationResultSerializer.to_json(r) for r in results]
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serialized_results, f, ensure_ascii=False, indent=2) 