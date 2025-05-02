"""
Unified output format for validation results across static and dynamic modes.
This module defines the schema and utilities for consistent validation output.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import json
import time
from pathlib import Path
import jsonschema
from datetime import datetime

class ValidationStatus(str, Enum):
    """Possible validation status values"""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    ERROR = "error"

class ValidationLevel(str, Enum):
    """Levels at which validation can occur"""
    DOCUMENT = "document"
    CATEGORY = "category"
    ITEM = "item"

@dataclass
class ValidationMetadata:
    """Metadata about the validation process"""
    timestamp: float = field(default_factory=time.time)
    validator_version: str = "1.0.0"
    mode: str = "static"  # static or dynamic
    confidence_score: float = 1.0
    processing_time_ms: float = 0.0
    warnings: List[str] = field(default_factory=list)

@dataclass
class ValidationItem:
    """Individual validation item result"""
    id: str
    name: str
    status: ValidationStatus
    confidence_score: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class ValidationCategory:
    """Category-level validation results"""
    id: str
    name: str
    status: ValidationStatus
    confidence_score: float = 1.0
    items: List[ValidationItem] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    """Complete validation result for a document"""
    document_id: str
    document_name: str
    document_type: str
    status: ValidationStatus
    metadata: ValidationMetadata
    categories: List[ValidationCategory] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

# JSON Schema for validation
VALIDATION_SCHEMA = {
    "type": "object",
    "required": ["document_id", "document_name", "document_type", "status", "metadata", "categories"],
    "properties": {
        "document_id": {"type": "string"},
        "document_name": {"type": "string"},
        "document_type": {"type": "string"},
        "status": {"type": "string", "enum": [s.value for s in ValidationStatus]},
        "metadata": {
            "type": "object",
            "required": ["timestamp", "validator_version", "mode"],
            "properties": {
                "timestamp": {"type": "number"},
                "validator_version": {"type": "string"},
                "mode": {"type": "string", "enum": ["static", "dynamic"]},
                "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                "processing_time_ms": {"type": "number"},
                "warnings": {"type": "array", "items": {"type": "string"}}
            }
        },
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name", "status"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": [s.value for s in ValidationStatus]},
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "status"],
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"},
                                "status": {"type": "string", "enum": [s.value for s in ValidationStatus]},
                                "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                                "details": {"type": "object"},
                                "errors": {"type": "array", "items": {"type": "string"}},
                                "warnings": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "errors": {"type": "array", "items": {"type": "string"}},
                    "warnings": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "errors": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}}
    }
}

class ValidationResultFormatter:
    """Handles formatting and output of validation results"""
    
    @staticmethod
    def to_dict(result: ValidationResult) -> Dict[str, Any]:
        """Convert ValidationResult to dictionary"""
        return {
            "document_id": result.document_id,
            "document_name": result.document_name,
            "document_type": result.document_type,
            "status": result.status.value,
            "metadata": {
                "timestamp": result.metadata.timestamp,
                "validator_version": result.metadata.validator_version,
                "mode": result.metadata.mode,
                "confidence_score": result.metadata.confidence_score,
                "processing_time_ms": result.metadata.processing_time_ms,
                "warnings": result.metadata.warnings
            },
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name,
                    "status": cat.status.value,
                    "confidence_score": cat.confidence_score,
                    "items": [
                        {
                            "id": item.id,
                            "name": item.name,
                            "status": item.status.value,
                            "confidence_score": item.confidence_score,
                            "details": item.details,
                            "errors": item.errors,
                            "warnings": item.warnings
                        }
                        for item in cat.items
                    ],
                    "errors": cat.errors,
                    "warnings": cat.warnings
                }
                for cat in result.categories
            ],
            "errors": result.errors,
            "warnings": result.warnings
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ValidationResult:
        """Convert dictionary to ValidationResult"""
        metadata = ValidationMetadata(
            timestamp=data["metadata"]["timestamp"],
            validator_version=data["metadata"]["validator_version"],
            mode=data["metadata"]["mode"],
            confidence_score=data["metadata"].get("confidence_score", 1.0),
            processing_time_ms=data["metadata"].get("processing_time_ms", 0.0),
            warnings=data["metadata"].get("warnings", [])
        )
        
        categories = []
        for cat_data in data["categories"]:
            items = [
                ValidationItem(
                    id=item["id"],
                    name=item["name"],
                    status=ValidationStatus(item["status"]),
                    confidence_score=item.get("confidence_score", 1.0),
                    details=item.get("details", {}),
                    errors=item.get("errors", []),
                    warnings=item.get("warnings", [])
                )
                for item in cat_data["items"]
            ]
            
            categories.append(
                ValidationCategory(
                    id=cat_data["id"],
                    name=cat_data["name"],
                    status=ValidationStatus(cat_data["status"]),
                    confidence_score=cat_data.get("confidence_score", 1.0),
                    items=items,
                    errors=cat_data.get("errors", []),
                    warnings=cat_data.get("warnings", [])
                )
            )
        
        return ValidationResult(
            document_id=data["document_id"],
            document_name=data["document_name"],
            document_type=data["document_type"],
            status=ValidationStatus(data["status"]),
            metadata=metadata,
            categories=categories,
            errors=data.get("errors", []),
            warnings=data.get("warnings", [])
        )
    
    @staticmethod
    def validate_schema(data: Dict[str, Any]) -> List[str]:
        """Validate data against the schema"""
        try:
            jsonschema.validate(instance=data, schema=VALIDATION_SCHEMA)
            return []
        except jsonschema.exceptions.ValidationError as e:
            return [str(e)]
    
    @staticmethod
    def save_to_file(result: ValidationResult, output_path: Path, pretty: bool = True) -> None:
        """Save validation result to file"""
        data = ValidationResultFormatter.to_dict(result)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False)
    
    @staticmethod
    def load_from_file(input_path: Path) -> ValidationResult:
        """Load validation result from file"""
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ValidationResultFormatter.from_dict(data)
    
    @staticmethod
    def filter_results(result: ValidationResult, 
                      status: Optional[ValidationStatus] = None,
                      min_confidence: float = 0.0,
                      include_warnings: bool = True) -> ValidationResult:
        """Filter validation results based on criteria"""
        filtered_categories = []
        
        for category in result.categories:
            if status and category.status != status:
                continue
            if category.confidence_score < min_confidence:
                continue
                
            filtered_items = [
                item for item in category.items
                if (not status or item.status == status) and
                   item.confidence_score >= min_confidence
            ]
            
            if not filtered_items and not include_warnings:
                continue
                
            filtered_categories.append(
                ValidationCategory(
                    id=category.id,
                    name=category.name,
                    status=category.status,
                    confidence_score=category.confidence_score,
                    items=filtered_items,
                    errors=category.errors if include_warnings else [],
                    warnings=category.warnings if include_warnings else []
                )
            )
        
        return ValidationResult(
            document_id=result.document_id,
            document_name=result.document_name,
            document_type=result.document_type,
            status=result.status,
            metadata=result.metadata,
            categories=filtered_categories,
            errors=result.errors if include_warnings else [],
            warnings=result.warnings if include_warnings else []
        )
    
    @staticmethod
    def pretty_print(result: ValidationResult) -> str:
        """Generate human-readable output"""
        output = []
        output.append(f"Document: {result.document_name} ({result.document_type})")
        output.append(f"Status: {result.status.value}")
        output.append(f"Confidence: {result.metadata.confidence_score:.2f}")
        output.append(f"Mode: {result.metadata.mode}")
        output.append(f"Timestamp: {datetime.fromtimestamp(result.metadata.timestamp)}")
        
        if result.warnings:
            output.append("\nDocument Warnings:")
            for warning in result.warnings:
                output.append(f"  ⚠ {warning}")
        
        if result.errors:
            output.append("\nDocument Errors:")
            for error in result.errors:
                output.append(f"  ✗ {error}")
        
        for category in result.categories:
            output.append(f"\nCategory: {category.name}")
            output.append(f"Status: {category.status.value}")
            output.append(f"Confidence: {category.confidence_score:.2f}")
            
            if category.warnings:
                output.append("  Category Warnings:")
                for warning in category.warnings:
                    output.append(f"    ⚠ {warning}")
            
            if category.errors:
                output.append("  Category Errors:")
                for error in category.errors:
                    output.append(f"    ✗ {error}")
            
            for item in category.items:
                output.append(f"\n  Item: {item.name}")
                output.append(f"  Status: {item.status.value}")
                output.append(f"  Confidence: {item.confidence_score:.2f}")
                
                if item.warnings:
                    output.append("    Item Warnings:")
                    for warning in item.warnings:
                        output.append(f"      ⚠ {warning}")
                
                if item.errors:
                    output.append("    Item Errors:")
                    for error in item.errors:
                        output.append(f"      ✗ {error}")
        
        return "\n".join(output) 