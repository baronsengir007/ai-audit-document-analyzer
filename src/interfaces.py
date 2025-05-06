"""
Core interfaces and data types for the AI Audit Document Scanner
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
import yaml

@dataclass
class Document:
    """Represents a document to be analyzed"""
    filename: str
    content: str
    classification: str
    metadata: Dict[str, Any]
    source_path: Optional[str] = None

@dataclass
class ComplianceResult:
    """Result of a compliance check"""
    is_compliant: bool
    confidence: float
    details: Dict[str, Any]
    mode_used: str

@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    issues: list[str]
    details: Dict[str, Any]

class DocumentProcessor(ABC):
    """Abstract base class for document processing"""
    @abstractmethod
    def process_document(self, doc_path: Path) -> Document:
        """Process a document and return unified Document object"""
        pass

class ValidationStrategy(ABC):
    """Abstract base class for validation strategies"""
    @abstractmethod
    def validate(self, document: Document) -> ValidationResult:
        """Validate a document and return unified ValidationResult"""
        pass

    @abstractmethod
    def get_checklist(self) -> Dict[str, Any]:
        """Get the checklist used for validation"""
        pass

class ValidationMode(ABC):
    """Abstract base class for validation modes"""
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the validation mode with configuration"""
        pass

    @abstractmethod
    def process_batch(self, documents: List[Document]) -> List[ValidationResult]:
        """Process a batch of documents"""
        pass

    @abstractmethod
    def save_results(self, results: List[ValidationResult], output_path: Path) -> None:
        """Save validation results"""
        pass

class ValidationResultSerializer:
    """Handles serialization/deserialization of validation results"""
    @staticmethod
    def to_json(result: ValidationResult) -> Dict[str, Any]:
        """Convert ValidationResult to JSON-serializable dict"""
        return {
            "document": {
                "filename": result.document.filename,
                "classification": result.document.classification,
                "metadata": result.document.metadata
            },
            "status": result.status,
            "validation_results": result.validation_results,
            "mode": result.mode,
            "timestamp": result.timestamp,
            "error": result.error
        }

    @staticmethod
    def from_json(data: Dict[str, Any]) -> ValidationResult:
        """Convert JSON dict to ValidationResult"""
        return ValidationResult(
            document=Document(
                filename=data["document"]["filename"],
                content="",  # Content not serialized for efficiency
                classification=data["document"]["classification"],
                metadata=data["document"]["metadata"]
            ),
            status=data["status"],
            validation_results=data["validation_results"],
            mode=data["mode"],
            timestamp=data["timestamp"],
            error=data.get("error")
        ) 