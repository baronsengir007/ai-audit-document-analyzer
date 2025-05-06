"""
Standalone Output Formatter Demonstration

This script demonstrates the compliance matrix output formatting capabilities 
without relying on imports from the main codebase. It includes minimal implementations
of the core classes needed to demonstrate the formatter functionality.
"""

import json
import csv
import os
import sys
import datetime
import tempfile
import shutil
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union

# === Minimal implementations of core classes for demonstration ===

class ValidationStatus(str, Enum):
    """Possible validation status values"""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    ERROR = "error"

class ComplianceLevel(str, Enum):
    """Levels of compliance for evaluation results"""
    FULLY_COMPLIANT = "fully_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"
    INDETERMINATE = "indeterminate"

class OutputFormat(str, Enum):
    """Supported output formats"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    MARKDOWN = "markdown"

class OutputType(str, Enum):
    """Types of compliance output"""
    DOCUMENT = "document"      # Single document output
    MATRIX = "matrix"          # Matrix comparing multiple documents/requirements
    SUMMARY = "summary"        # Summary statistics only

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
class ValidationMetadata:
    """Metadata about the validation process"""
    timestamp: float = field(default_factory=lambda: datetime.datetime.now().timestamp())
    validator_version: str = "1.0.0"
    mode: str = "static"  # static or dynamic
    confidence_score: float = 1.0
    processing_time_ms: float = 0.0
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

@dataclass
class ComplianceResult:
    """Simplified compliance result object for demonstration"""
    is_compliant: bool
    confidence: float
    details: Dict[str, Any] = field(default_factory=dict)

# === OutputFormatter Implementation ===

class OutputFormatter:
    """
    Unified formatter for compliance results with support for multiple output formats.
    
    This class provides a simplified demonstration of the output formatting capabilities
    for the compliance matrix implementation.
    """
    
    def __init__(
        self,
        include_details=True,
        include_justifications=True,
        include_confidence=True,
        include_metadata=True
    ):
        """Initialize the formatter with configuration options"""
        self.include_details = include_details
        self.include_justifications = include_justifications
        self.include_confidence = include_confidence
        self.include_metadata = include_metadata
        
        # Color mapping for different statuses
        self.status_colors = {
            "passed": "#4CAF50",      # Green
            "partial": "#FFC107",     # Amber
            "failed": "#F44336",      # Red
            "unknown": "#9E9E9E",     # Grey
            "error": "#9C27B0"        # Purple
        }
        
        # Symbol mapping for different statuses
        self.status_symbols = {
            "passed": "✓",
            "partial": "⚠",
            "failed": "✗",
            "unknown": "?",
            "error": "!"
        }
    
    def format_document(
        self,
        result,
        output_format=OutputFormat.JSON,
        output_path=None
    ):
        """Format a document result in the specified format"""
        if output_format == OutputFormat.JSON:
            formatted = self._format_document_json(result)
            if output_path:
                self._save_json(formatted, output_path)
            return formatted
            
        elif output_format == OutputFormat.CSV:
            csv_content = self._format_document_csv(result)
            if output_path:
                self._save_text(csv_content, output_path)
            return csv_content
            
        elif output_format == OutputFormat.HTML:
            html_content = self._format_document_html(result)
            if output_path:
                self._save_text(html_content, output_path)
            return html_content
            
        elif output_format == OutputFormat.MARKDOWN:
            md_content = self._format_document_markdown(result)
            if output_path:
                self._save_text(md_content, output_path)
            return md_content
            
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def format_matrix(
        self,
        documents,
        requirements,
        compliance_matrix,
        output_format=OutputFormat.JSON,
        output_path=None
    ):
        """Format a compliance matrix in the specified format"""
        if output_format == OutputFormat.JSON:
            formatted = self._format_matrix_json(documents, requirements, compliance_matrix)
            if output_path:
                self._save_json(formatted, output_path)
            return formatted
            
        elif output_format == OutputFormat.CSV:
            csv_content = self._format_matrix_csv(documents, requirements, compliance_matrix)
            if output_path:
                self._save_text(csv_content, output_path)
            return csv_content
            
        elif output_format == OutputFormat.HTML:
            html_content = self._format_matrix_html(documents, requirements, compliance_matrix)
            if output_path:
                self._save_text(html_content, output_path)
            return html_content
            
        elif output_format == OutputFormat.MARKDOWN:
            md_content = self._format_matrix_markdown(documents, requirements, compliance_matrix)
            if output_path:
                self._save_text(md_content, output_path)
            return md_content
            
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def format_summary(
        self,
        data,
        output_format=OutputFormat.JSON,
        output_path=None
    ):
        """Format a summary report in the specified format"""
        if output_format == OutputFormat.JSON:
            formatted = self._format_summary_json(data)
            if output_path:
                self._save_json(formatted, output_path)
            return formatted
            
        elif output_format == OutputFormat.CSV:
            csv_content = self._format_summary_csv(data)
            if output_path:
                self._save_text(csv_content, output_path)
            return csv_content
            
        elif output_format == OutputFormat.HTML:
            html_content = self._format_summary_html(data)
            if output_path:
                self._save_text(html_content, output_path)
            return html_content
            
        elif output_format == OutputFormat.MARKDOWN:
            md_content = self._format_summary_markdown(data)
            if output_path:
                self._save_text(md_content, output_path)
            return md_content
            
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    # === JSON Formatters ===
    
    def _format_document_json(self, result):
        """Format a document result as JSON"""
        if isinstance(result, ValidationResult):
            # Convert ValidationResult to dictionary
            return {
                "document_id": result.document_id,
                "document_name": result.document_name,
                "document_type": result.document_type,
                "status": result.status,
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
                        "status": cat.status,
                        "confidence_score": cat.confidence_score,
                        "items": [
                            {
                                "id": item.id,
                                "name": item.name,
                                "status": item.status,
                                "confidence_score": item.confidence_score,
                                "details": item.details if self.include_details else {},
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
        elif isinstance(result, dict):
            # If already a dictionary, return it unchanged
            return result
        else:
            raise TypeError(f"Unsupported result type: {type(result)}")
    
    def _format_matrix_json(self, documents, requirements, compliance_matrix):
        """Format a compliance matrix as JSON"""
        # Create a structured JSON representation of the matrix
        return {
            "metadata": {
                "timestamp": datetime.datetime.now().timestamp(),
                "version": "1.0.0",
                "generated_by": "OutputFormatter"
            },
            "documents": documents,
            "requirements": requirements,
            "compliance_matrix": compliance_matrix,
            "summary": self._generate_matrix_summary(documents, requirements, compliance_matrix)
        }
    
    def _format_summary_json(self, data):
        """Format a summary report as JSON"""
        if isinstance(data, ValidationResult):
            # Generate summary from validation result
            status_counts = {"passed": 0, "partial": 0, "failed": 0, "unknown": 0, "error": 0}
            category_summary = {}
            
            # Count statuses across categories
            for category in data.categories:
                cat_statuses = {"passed": 0, "partial": 0, "failed": 0, "unknown": 0, "error": 0}
                
                for item in category.items:
                    status = item.status
                    cat_statuses[status] += 1
                    status_counts[status] += 1
                
                category_summary[category.name] = {
                    "status": category.status,
                    "confidence": category.confidence_score,
                    "item_count": len(category.items),
                    "item_statuses": cat_statuses
                }
            
            return {
                "document_id": data.document_id,
                "document_name": data.document_name,
                "document_type": data.document_type,
                "status": data.status,
                "confidence": data.metadata.confidence_score,
                "mode": data.metadata.mode,
                "timestamp": data.metadata.timestamp,
                "status_counts": status_counts,
                "category_summary": category_summary
            }
        elif isinstance(data, dict):
            # If it's already a dictionary with documents, requirements, etc.
            return {
                "metadata": {
                    "timestamp": datetime.datetime.now().timestamp(),
                    "version": "1.0.0"
                },
                "overall_compliance": self._calculate_overall_compliance(data),
                "document_summary": self._summarize_documents(data.get("documents", [])),
                "requirement_summary": self._summarize_requirements(data.get("requirements", []))
            }
        else:
            raise TypeError(f"Unsupported data type for summary: {type(data)}")
    
    # === CSV Formatters ===
    
    def _format_document_csv(self, result):
        """Format a document result as CSV"""
        output = []
        
        # Header information
        output.append(f"Document ID,{result.document_id}")
        output.append(f"Document Name,{result.document_name}")
        output.append(f"Document Type,{result.document_type}")
        output.append(f"Overall Status,{result.status}")
        
        if self.include_confidence:
            output.append(f"Confidence,{result.metadata.confidence_score:.2f}")
            
        output.append(f"Mode,{result.metadata.mode}")
        output.append(f"Timestamp,{datetime.datetime.fromtimestamp(result.metadata.timestamp).isoformat()}")
        output.append("")
        
        # Categories and items
        output.append("Category,Status,Confidence,Item ID,Item Name,Item Status,Item Confidence,Justification")
        
        for category in result.categories:
            # First item in category with category info
            if category.items:
                first_item = category.items[0]
                justification = first_item.details.get("justification", "") if self.include_justifications else ""
                
                output.append(
                    f"{category.name},{category.status},{category.confidence_score:.2f}," +
                    f"{first_item.id},{first_item.name},{first_item.status}," +
                    f"{first_item.confidence_score:.2f},{justification}"
                )
                
                # Remaining items with empty category cells
                for item in category.items[1:]:
                    justification = item.details.get("justification", "") if self.include_justifications else ""
                    
                    output.append(
                        f",,," +
                        f"{item.id},{item.name},{item.status}," +
                        f"{item.confidence_score:.2f},{justification}"
                    )
            else:
                # Category with no items
                output.append(f"{category.name},{category.status},{category.confidence_score:.2f},,,,")
            
            output.append("")
            
        return "\n".join(output)
    
    def _format_matrix_csv(self, documents, requirements, compliance_matrix):
        """Format a compliance matrix as CSV"""
        output = []
        
        # Create header row with requirement IDs
        header = ["Document ID", "Document Name"]
        for req in requirements:
            header.append(req["id"])
        
        output.append(",".join(header))
        
        # Create document rows
        for doc in documents:
            row = [doc["id"], doc["name"]]
            
            # Find this document's compliance matrix entry
            matrix_entry = next((entry for entry in compliance_matrix if entry["document_id"] == doc["id"]), None)
            
            if matrix_entry:
                # Add a cell for each requirement
                for req in requirements:
                    req_id = req["id"]
                    result = matrix_entry["results"].get(req_id, {"compliance_level": "indeterminate"})
                    
                    # Format the cell based on compliance level
                    level = result["compliance_level"]
                    symbol = self._get_symbol_for_level(level)
                    
                    if self.include_confidence and "confidence_score" in result:
                        cell = f"{symbol} {level} ({result['confidence_score']:.2f})"
                    else:
                        cell = f"{symbol} {level}"
                    
                    row.append(cell)
            else:
                # If no results for this document, add empty cells
                row.extend([""] * len(requirements))
            
            output.append(",".join(row))
            
        # Add summary section
        output.append("")
        output.append("Summary")
        
        summary = self._generate_matrix_summary(documents, requirements, compliance_matrix)
        output.append(f"Overall Compliance,{summary['overall_compliance']}")
        
        for level, count in summary.get("compliance_counts", {}).items():
            output.append(f"{level},Count,{count}")
            
        return "\n".join(output)
    
    def _format_summary_csv(self, data):
        """Format a summary report as CSV"""
        output = []
        
        if isinstance(data, ValidationResult):
            # Generate summary from validation result
            output.append(f"Document ID,{data.document_id}")
            output.append(f"Document Name,{data.document_name}")
            output.append(f"Document Type,{data.document_type}")
            output.append(f"Overall Status,{data.status}")
            output.append(f"Confidence,{data.metadata.confidence_score:.2f}")
            output.append("")
            
            # Status counts
            output.append("Status Counts")
            status_counts = {"passed": 0, "partial": 0, "failed": 0, "unknown": 0, "error": 0}
            
            for category in data.categories:
                for item in category.items:
                    status_counts[item.status] += 1
            
            for status, count in status_counts.items():
                if count > 0:
                    output.append(f"{status.title()},{count}")
            
            output.append("")
            
            # Category summary
            output.append("Category,Status,Confidence,Items,Passed,Partial,Failed,Other")
            
            for category in data.categories:
                cat_statuses = {"passed": 0, "partial": 0, "failed": 0, "unknown": 0, "error": 0}
                
                for item in category.items:
                    cat_statuses[item.status] += 1
                
                other_count = cat_statuses["unknown"] + cat_statuses["error"]
                
                output.append(
                    f"{category.name},{category.status},{category.confidence_score:.2f}," +
                    f"{len(category.items)},{cat_statuses['passed']},{cat_statuses['partial']}," +
                    f"{cat_statuses['failed']},{other_count}"
                )
            
        else:
            # Summary for matrix data
            summary = self._format_summary_json(data)
            
            output.append("Matrix Summary")
            output.append(f"Overall Compliance,{summary.get('overall_compliance', 'unknown')}")
            output.append("")
            
            output.append("Document Summary")
            output.append("Document ID,Document Type,Status,Confidence")
            
            for doc in summary.get("document_summary", []):
                output.append(
                    f"{doc['id']},{doc['type']},{doc['status']}," +
                    f"{doc.get('confidence', 0):.2f}"
                )
            
            output.append("")
            output.append("Requirement Summary")
            output.append("Requirement ID,Category,Type,Priority,Compliance")
            
            for req in summary.get("requirement_summary", []):
                output.append(
                    f"{req['id']},{req.get('category', '')},{req.get('type', '')}," +
                    f"{req.get('priority', '')},{req.get('compliance', '')}"
                )
            
        return "\n".join(output)
    
    # === HTML Formatters ===
    
    def _format_document_html(self, result):
        """Format a document result as HTML"""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("    <meta charset='UTF-8'>")
        html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append(f"    <title>Compliance Report - {result.document_name}</title>")
        html.append("    <style>")
        html.append("        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.5; }")
        html.append("        h1, h2, h3 { color: #333; }")
        html.append("        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }")
        html.append("        .header-title { flex-grow: 1; }")
        html.append("        .header-meta { background: #f5f5f5; padding: 10px; border-radius: 5px; font-size: 0.9em; }")
        html.append("        .document-info { margin-bottom: 30px; background: #f5f5f5; padding: 15px; border-radius: 5px; }")
        html.append("        .document-info table { width: 100%; border-collapse: collapse; }")
        html.append("        .document-info th { text-align: left; font-weight: normal; color: #666; width: 30%; }")
        html.append("        .status-badge { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; text-transform: uppercase; font-size: 0.8em; }")
        html.append("        .category { margin-bottom: 30px; border: 1px solid #ddd; border-radius: 5px; }")
        html.append("        .category-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; background: #f9f9f9; border-bottom: 1px solid #ddd; }")
        html.append("        .category-name { font-weight: bold; font-size: 1.1em; margin-right: 10px; }")
        html.append("        .category-status { display: flex; align-items: center; }")
        html.append("        .items-table { width: 100%; border-collapse: collapse; }")
        html.append("        .items-table th, .items-table td { text-align: left; padding: 10px; border-bottom: 1px solid #eee; }")
        html.append("        .items-table th { background: #f5f5f5; font-weight: 600; }")
        html.append("        .items-table tr:last-child td { border-bottom: none; }")
        html.append("        .items-table tr:hover { background: #f9f9f9; }")
        html.append("        .tooltip { position: relative; cursor: help; }")
        html.append("        .tooltip .tooltiptext { visibility: hidden; width: 200px; background-color: #333; color: #fff; text-align: center;")
        html.append("            border-radius: 6px; padding: 10px; position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -100px;")
        html.append("            opacity: 0; transition: opacity 0.3s; font-size: 0.9em; }")
        html.append("        .tooltip:hover .tooltiptext { visibility: visible; opacity: 0.9; }")
        
        # Add status-specific styles
        for status, color in self.status_colors.items():
            html.append(f"        .status-{status} {{ background-color: {color}; }}")
        
        html.append("    </style>")
        html.append("</head>")
        html.append("<body>")
        
        # Header
        html.append("    <div class='header'>")
        html.append("        <div class='header-title'>")
        html.append(f"            <h1>Compliance Report</h1>")
        html.append("        </div>")
        html.append("        <div class='header-meta'>")
        html.append(f"            Generated: {datetime.datetime.fromtimestamp(result.metadata.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        html.append("        </div>")
        html.append("    </div>")
        
        # Document Information
        html.append("    <div class='document-info'>")
        html.append("        <h2>Document Information</h2>")
        html.append("        <table>")
        html.append("            <tr>")
        html.append("                <th>Document Name:</th>")
        html.append(f"                <td>{result.document_name}</td>")
        html.append("            </tr>")
        html.append("            <tr>")
        html.append("                <th>Document ID:</th>")
        html.append(f"                <td>{result.document_id}</td>")
        html.append("            </tr>")
        html.append("            <tr>")
        html.append("                <th>Document Type:</th>")
        html.append(f"                <td>{result.document_type}</td>")
        html.append("            </tr>")
        html.append("            <tr>")
        html.append("                <th>Overall Status:</th>")
        status = result.status
        status_symbol = self.status_symbols.get(status, "?")
        html.append(f"                <td><span class='status-badge status-{status}'>{status_symbol} {status.upper()}</span></td>")
        html.append("            </tr>")
        
        if self.include_confidence:
            html.append("            <tr>")
            html.append("                <th>Confidence Score:</th>")
            confidence = result.metadata.confidence_score
            html.append(f"                <td>{confidence:.2f}</td>")
            html.append("            </tr>")
        
        html.append("            <tr>")
        html.append("                <th>Validation Mode:</th>")
        html.append(f"                <td>{result.metadata.mode}</td>")
        html.append("            </tr>")
        html.append("        </table>")
        html.append("    </div>")
        
        # Categories and Items
        html.append("    <h2>Validation Results</h2>")
        
        for category in result.categories:
            cat_status = category.status
            cat_symbol = self.status_symbols.get(cat_status, "?")
            
            html.append(f"    <div class='category'>")
            html.append(f"        <div class='category-header'>")
            html.append(f"            <div class='category-name'>{category.name}</div>")
            html.append(f"            <div class='category-status'>")
            html.append(f"                <span class='status-badge status-{cat_status}'>{cat_symbol} {cat_status.upper()}</span>")
            
            if self.include_confidence:
                confidence = category.confidence_score
                html.append(f"                <span style='margin-left: 10px;'>(Confidence: {confidence:.2f})</span>")
                
            html.append(f"            </div>")
            html.append(f"        </div>")
            
            if category.items:
                html.append(f"        <table class='items-table'>")
                html.append(f"            <thead>")
                html.append(f"                <tr>")
                html.append(f"                    <th>Item</th>")
                html.append(f"                    <th>Status</th>")
                
                if self.include_confidence:
                    html.append(f"                    <th>Confidence</th>")
                    
                if self.include_justifications:
                    html.append(f"                    <th>Justification</th>")
                    
                html.append(f"                </tr>")
                html.append(f"            </thead>")
                html.append(f"            <tbody>")
                
                for item in category.items:
                    item_status = item.status
                    item_symbol = self.status_symbols.get(item_status, "?")
                    
                    html.append(f"                <tr>")
                    html.append(f"                    <td>{item.name}")
                    
                    # Add tooltip with item ID if details are included
                    if self.include_details:
                        html.append(f" <span class='tooltip'>ℹ")
                        html.append(f"                        <span class='tooltiptext'>ID: {item.id}</span>")
                        html.append(f"                    </span>")
                    
                    html.append(f"                    </td>")
                    html.append(f"                    <td><span class='status-badge status-{item_status}'>{item_symbol} {item_status.upper()}</span></td>")
                    
                    if self.include_confidence:
                        confidence = item.confidence_score
                        html.append(f"                    <td>{confidence:.2f}</td>")
                        
                    if self.include_justifications:
                        justification = item.details.get("justification", "")
                        html.append(f"                    <td>{justification}</td>")
                        
                    html.append(f"                </tr>")
                
                html.append(f"            </tbody>")
                html.append(f"        </table>")
            else:
                html.append(f"        <p style='padding: 15px; color: #666;'>No items in this category.</p>")
                
            html.append(f"    </div>")
        
        # Errors and Warnings
        if result.errors or result.warnings:
            html.append("    <h2>Issues</h2>")
            
            if result.errors:
                html.append("    <div style='margin-bottom: 15px;'>")
                html.append("        <h3>Errors</h3>")
                html.append("        <ul>")
                for error in result.errors:
                    html.append(f"            <li style='color: #F44336;'>{error}</li>")
                html.append("        </ul>")
                html.append("    </div>")
                
            if result.warnings:
                html.append("    <div>")
                html.append("        <h3>Warnings</h3>")
                html.append("        <ul>")
                for warning in result.warnings:
                    html.append(f"            <li style='color: #FFC107;'>{warning}</li>")
                html.append("        </ul>")
                html.append("    </div>")
        
        # Metadata footer
        if self.include_metadata:
            html.append("    <div style='margin-top: 30px; border-top: 1px solid #eee; padding-top: 15px; color: #999; font-size: 0.8em;'>")
            html.append("        <p>")
            html.append(f"            Validator Version: {result.metadata.validator_version}<br>")
            html.append(f"            Processing Time: {result.metadata.processing_time_ms:.2f} ms<br>")
            html.append(f"            Timestamp: {datetime.datetime.fromtimestamp(result.metadata.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            html.append("        </p>")
            html.append("    </div>")
        
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    def _format_matrix_html(self, documents, requirements, compliance_matrix):
        """Format a compliance matrix as HTML"""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("    <meta charset='UTF-8'>")
        html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("    <title>Compliance Matrix</title>")
        html.append("    <style>")
        html.append("        body { font-family: Arial, sans-serif; margin: 20px; }")
        html.append("        h1, h2 { color: #333; }")
        html.append("        table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }")
        html.append("        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html.append("        th { background-color: #f2f2f2; position: sticky; top: 0; }")
        html.append("        tr:nth-child(even) { background-color: #f9f9f9; }")
        html.append("        tr:hover { background-color: #f2f2f2; }")
        html.append("        .header-row th { text-align: center; font-weight: bold; }")
        html.append("        .tooltip { position: relative; display: inline-block; }")
        html.append("        .tooltip .tooltiptext { visibility: hidden; width: 200px; background-color: #555;")
        html.append("                             color: #fff; text-align: center; border-radius: 6px;")
        html.append("                             padding: 5px; position: absolute; z-index: 1;")
        html.append("                             bottom: 125%; left: 50%; margin-left: -100px;")
        html.append("                             opacity: 0; transition: opacity 0.3s; }")
        html.append("        .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }")
        
        # Add compliance level colors
        html.append("        .fully_compliant { background-color: #4CAF50; color: white; text-align: center; }")
        html.append("        .partially_compliant { background-color: #FFC107; text-align: center; }")
        html.append("        .non_compliant { background-color: #F44336; color: white; text-align: center; }")
        html.append("        .not_applicable { background-color: #9E9E9E; color: white; text-align: center; }")
        html.append("        .indeterminate { background-color: #2196F3; color: white; text-align: center; }")
        
        html.append("    </style>")
        html.append("</head>")
        html.append("<body>")
        html.append("    <h1>Compliance Matrix Report</h1>")
        html.append(f"    <p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        
        # Main matrix table
        html.append("    <h2>Compliance Matrix</h2>")
        html.append("    <table>")
        
        # Table header with requirement IDs
        html.append("        <tr class='header-row'>")
        html.append("            <th rowspan='2'>Document ID</th>")
        html.append("            <th rowspan='2'>Document Name</th>")
        html.append(f"            <th colspan='{len(requirements)}'>Requirements</th>")
        html.append("        </tr>")
        
        html.append("        <tr>")
        for req in requirements:
            req_id = req["id"]
            description = req.get("description", "")
            req_type = req.get("type", "")
            priority = req.get("priority", "")
            
            # Create tooltip with requirement details
            tooltip = f"Type: {req_type}<br>Priority: {priority}<br>Description: {description}"
            html.append(f"            <th><div class='tooltip'>{req_id}<span class='tooltiptext'>{tooltip}</span></div></th>")
        html.append("        </tr>")
        
        # Generate rows for each document
        for doc in documents:
            doc_id = doc["id"]
            doc_name = doc.get("name", doc_id)
            
            html.append("        <tr>")
            html.append(f"            <td>{doc_id}</td>")
            html.append(f"            <td>{doc_name}</td>")
            
            # Find this document's compliance matrix entry
            matrix_entry = next((entry for entry in compliance_matrix if entry["document_id"] == doc_id), None)
            
            if matrix_entry:
                # Add a cell for each requirement
                for req in requirements:
                    req_id = req["id"]
                    result = matrix_entry["results"].get(req_id, {"compliance_level": "indeterminate"})
                    
                    # Get the compliance level (default to "indeterminate")
                    level = result.get("compliance_level", "indeterminate")
                    
                    # Get justification if available
                    justification = result.get("justification", "No justification provided")
                    confidence = result.get("confidence_score", 0.0)
                    
                    # Format the cell based on visualization style
                    symbol = self._get_symbol_for_level(level)
                    cell_content = symbol
                    
                    # Add confidence score if requested
                    if self.include_confidence:
                        cell_content = f"{cell_content} ({confidence:.2f})"
                    
                    # Create a tooltip with justification if requested
                    if self.include_justifications:
                        tooltip = f"<span class='tooltiptext'>{justification}</span>"
                        cell_content = f"<div class='tooltip'>{cell_content}{tooltip}</div>"
                    
                    # Add the cell with appropriate styling
                    html.append(f"            <td class='{level}'>{cell_content}</td>")
            else:
                # If no results for this document, add empty cells
                for _ in requirements:
                    html.append("            <td></td>")
            
            html.append("        </tr>")
        
        html.append("    </table>")
        
        # Add summary section
        html.append("    <h2>Summary</h2>")
        
        summary = self._generate_matrix_summary(documents, requirements, compliance_matrix)
        
        html.append("    <table class='summary-table'>")
        html.append("        <tr>")
        html.append("            <th>Overall Compliance:</th>")
        overall_level = summary.get("overall_compliance", "indeterminate")
        html.append(f"            <td class='{overall_level}'>{overall_level.replace('_', ' ').title()}</td>")
        html.append("        </tr>")
        
        # Add counts for each compliance level
        for level, count in summary.get("compliance_counts", {}).items():
            percentage = summary.get("compliance_percentages", {}).get(level, 0)
            
            html.append("        <tr>")
            html.append(f"            <th>{level.replace('_', ' ').title()}:</th>")
            html.append(f"            <td>{count} ({percentage:.1f}%)</td>")
            html.append("        </tr>")
        
        html.append("    </table>")
        
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    def _format_summary_html(self, data):
        """Format a summary report as HTML with visualizations"""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("    <meta charset='UTF-8'>")
        html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("    <title>Compliance Summary</title>")
        html.append("    <style>")
        html.append("        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.5; }")
        html.append("        h1, h2, h3 { color: #333; }")
        html.append("        .section { margin-bottom: 30px; }")
        html.append("        .status-badge { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; text-transform: uppercase; font-size: 0.8em; }")
        html.append("        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }")
        html.append("        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #eee; }")
        html.append("        th { background: #f5f5f5; font-weight: 600; }")
        html.append("        .chart-container { position: relative; height: 200px; margin-bottom: 20px; }")
        
        # Add status-specific styles
        for status, color in self.status_colors.items():
            html.append(f"        .status-{status} {{ background-color: {color}; }}")
            
        html.append("    </style>")
        html.append("</head>")
        html.append("<body>")
        
        if isinstance(data, ValidationResult):
            # Summary from validation result
            status_counts = {"passed": 0, "partial": 0, "failed": 0, "unknown": 0, "error": 0}
            
            # Count statuses across categories
            for category in data.categories:
                for item in category.items:
                    status_counts[item.status] += 1
            
            # Header
            html.append(f"    <h1>Compliance Summary: {data.document_name}</h1>")
            html.append(f"    <p>Generated: {datetime.datetime.fromtimestamp(data.metadata.timestamp).strftime('%Y-%m-%d %H:%M:%S')}</p>")
            
            # Document info
            html.append("    <div class='section'>")
            html.append("        <h2>Document Information</h2>")
            html.append("        <table>")
            html.append(f"            <tr><th>Document ID</th><td>{data.document_id}</td></tr>")
            html.append(f"            <tr><th>Document Type</th><td>{data.document_type}</td></tr>")
            html.append(f"            <tr><th>Overall Status</th><td><span class='status-badge status-{data.status}'>{data.status.upper()}</span></td></tr>")
            html.append(f"            <tr><th>Confidence</th><td>{data.metadata.confidence_score:.2f}</td></tr>")
            html.append(f"            <tr><th>Mode</th><td>{data.metadata.mode}</td></tr>")
            html.append("        </table>")
            html.append("    </div>")
            
            # Status chart
            html.append("    <div class='section'>")
            html.append("        <h2>Status Distribution</h2>")
            html.append("        <div class='chart-container'>")
            html.append("            <div style='display: flex; height: 100%;'>")
            
            total_items = sum(status_counts.values())
            for status, count in status_counts.items():
                if total_items > 0:
                    width = (count / total_items) * 100
                else:
                    width = 0
                    
                html.append(f"                <div class='status-{status}' style='width: {width}%; height: 100%; position: relative;'>")
                if width >= 5:  # Only show text if bar is wide enough
                    html.append(f"                    <div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white;'>{count}</div>")
                html.append(f"                </div>")
                
            html.append("            </div>")
            html.append("        </div>")
            
            # Status table
            html.append("        <table>")
            html.append("            <tr><th>Status</th><th>Count</th><th>Percentage</th></tr>")
            
            for status, count in status_counts.items():
                if total_items > 0:
                    percentage = (count / total_items) * 100
                else:
                    percentage = 0
                    
                html.append("            <tr>")
                html.append(f"                <td><span class='status-badge status-{status}'>{status.upper()}</span></td>")
                html.append(f"                <td>{count}</td>")
                html.append(f"                <td>{percentage:.1f}%</td>")
                html.append("            </tr>")
                
            html.append("        </table>")
            html.append("    </div>")
            
            # Category breakdown
            html.append("    <div class='section'>")
            html.append("        <h2>Category Breakdown</h2>")
            html.append("        <table>")
            html.append("            <tr>")
            html.append("                <th>Category</th>")
            html.append("                <th>Status</th>")
            html.append("                <th>Items</th>")
            html.append("                <th>Passed</th>")
            html.append("                <th>Partial</th>")
            html.append("                <th>Failed</th>")
            html.append("                <th>Other</th>")
            html.append("            </tr>")
            
            for category in data.categories:
                cat_statuses = {"passed": 0, "partial": 0, "failed": 0, "unknown": 0, "error": 0}
                
                for item in category.items:
                    cat_statuses[item.status] += 1
                
                other_count = cat_statuses["unknown"] + cat_statuses["error"]
                
                html.append("            <tr>")
                html.append(f"                <td>{category.name}</td>")
                html.append(f"                <td><span class='status-badge status-{category.status}'>{category.status.upper()}</span></td>")
                html.append(f"                <td>{len(category.items)}</td>")
                html.append(f"                <td>{cat_statuses['passed']}</td>")
                html.append(f"                <td>{cat_statuses['partial']}</td>")
                html.append(f"                <td>{cat_statuses['failed']}</td>")
                html.append(f"                <td>{other_count}</td>")
                html.append("            </tr>")
                
            html.append("        </table>")
            html.append("    </div>")
            
        else:
            # Summary for matrix data
            summary = self._format_summary_json(data) if isinstance(data, dict) else data
            
            # Header
            html.append("    <h1>Compliance Matrix Summary</h1>")
            html.append(f"    <p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
            
            # Overall compliance
            html.append("    <div class='section'>")
            html.append("        <h2>Overall Compliance</h2>")
            overall = summary.get("overall_compliance", "indeterminate")
            html.append(f"        <p><span class='status-badge status-{overall.replace('_', '')}'>{overall.replace('_', ' ').upper()}</span></p>")
            html.append("    </div>")
            
            # Document summary
            html.append("    <div class='section'>")
            html.append("        <h2>Document Summary</h2>")
            html.append("        <table>")
            html.append("            <tr>")
            html.append("                <th>Document ID</th>")
            html.append("                <th>Document Type</th>")
            html.append("                <th>Status</th>")
            html.append("                <th>Confidence</th>")
            html.append("            </tr>")
            
            for doc in summary.get("document_summary", []):
                status = doc.get("status", "unknown")
                html.append("            <tr>")
                html.append(f"                <td>{doc['id']}</td>")
                html.append(f"                <td>{doc.get('type', '')}</td>")
                html.append(f"                <td><span class='status-badge status-{status.replace('_', '')}'>{status.replace('_', ' ').upper()}</span></td>")
                html.append(f"                <td>{doc.get('confidence', 0):.2f}</td>")
                html.append("            </tr>")
                
            html.append("        </table>")
            html.append("    </div>")
            
            # Requirement summary
            html.append("    <div class='section'>")
            html.append("        <h2>Requirement Summary</h2>")
            html.append("        <table>")
            html.append("            <tr>")
            html.append("                <th>Requirement ID</th>")
            html.append("                <th>Category</th>")
            html.append("                <th>Type</th>")
            html.append("                <th>Priority</th>")
            html.append("                <th>Compliance</th>")
            html.append("            </tr>")
            
            for req in summary.get("requirement_summary", []):
                compliance = req.get("compliance", "unknown")
                html.append("            <tr>")
                html.append(f"                <td>{req['id']}</td>")
                html.append(f"                <td>{req.get('category', '')}</td>")
                html.append(f"                <td>{req.get('type', '')}</td>")
                html.append(f"                <td>{req.get('priority', '')}</td>")
                html.append(f"                <td><span class='status-badge status-{compliance.replace('_', '')}'>{compliance.replace('_', ' ').upper()}</span></td>")
                html.append("            </tr>")
                
            html.append("        </table>")
            html.append("    </div>")
            
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    # === Markdown Formatters ===
    
    def _format_document_markdown(self, result):
        """Format a document result as Markdown"""
        md = []
        
        # Status to symbol mapping for markdown
        status_symbols = {
            "passed": "✅",
            "partial": "⚠️",
            "failed": "❌",
            "unknown": "❓",
            "error": "⛔"
        }
        
        # Document header
        md.append(f"# Compliance Report: {result.document_name}")
        md.append(f"Generated: {datetime.datetime.fromtimestamp(result.metadata.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")
        
        # Document information
        md.append("## Document Information")
        md.append("")
        md.append(f"**Document ID:** {result.document_id}")
        md.append(f"**Document Type:** {result.document_type}")
        
        status = result.status
        status_symbol = status_symbols.get(status, "❓")
        md.append(f"**Overall Status:** {status_symbol} {status.upper()}")
        
        if self.include_confidence:
            confidence = result.metadata.confidence_score
            md.append(f"**Confidence Score:** {confidence:.2f}")
            
        md.append(f"**Validation Mode:** {result.metadata.mode}")
        md.append("")
        
        # Categories and Items
        md.append("## Validation Results")
        md.append("")
        
        for category in result.categories:
            cat_status = category.status
            cat_symbol = status_symbols.get(cat_status, "❓")
            
            md.append(f"### {category.name} {cat_symbol} {cat_status.upper()}")
            
            if self.include_confidence:
                confidence = category.confidence_score
                md.append(f"Confidence: {confidence:.2f}")
                
            md.append("")
            
            if category.items:
                # Create table header based on what we're including
                headers = ["Item", "Status"]
                if self.include_confidence:
                    headers.append("Confidence")
                if self.include_justifications:
                    headers.append("Justification")
                    
                md.append("| " + " | ".join(headers) + " |")
                md.append("| " + " | ".join(["---"] * len(headers)) + " |")
                
                for item in category.items:
                    item_status = item.status
                    item_symbol = status_symbols.get(item_status, "❓")
                    
                    row = [
                        f"{item.name}" + (f" (ID: {item.id})" if self.include_details else ""),
                        f"{item_symbol} {item_status.upper()}"
                    ]
                    
                    if self.include_confidence:
                        confidence = item.confidence_score
                        row.append(f"{confidence:.2f}")
                        
                    if self.include_justifications:
                        justification = item.details.get("justification", "")
                        # Replace any | characters in justification to avoid breaking the table
                        justification = justification.replace("|", "\\|")
                        row.append(justification)
                        
                    md.append("| " + " | ".join(row) + " |")
            else:
                md.append("*No items in this category.*")
                
            md.append("")
        
        # Errors and Warnings
        if result.errors or result.warnings:
            md.append("## Issues")
            md.append("")
            
            if result.errors:
                md.append("### Errors")
                md.append("")
                for error in result.errors:
                    md.append(f"- ❌ {error}")
                md.append("")
                
            if result.warnings:
                md.append("### Warnings")
                md.append("")
                for warning in result.warnings:
                    md.append(f"- ⚠️ {warning}")
                md.append("")
        
        # Metadata footer
        if self.include_metadata:
            md.append("---")
            md.append(f"*Validator Version: {result.metadata.validator_version}*")
            md.append(f"*Processing Time: {result.metadata.processing_time_ms:.2f} ms*")
            md.append(f"*Timestamp: {datetime.datetime.fromtimestamp(result.metadata.timestamp).strftime('%Y-%m-%d %H:%M:%S')}*")
            
        return "\n".join(md)
    
    def _format_matrix_markdown(self, documents, requirements, compliance_matrix):
        """Format a compliance matrix as Markdown"""
        md = []
        
        # Symbol mapping for compliance levels
        level_symbols = {
            "fully_compliant": "✅",
            "partially_compliant": "⚠️",
            "non_compliant": "❌",
            "not_applicable": "➖",
            "indeterminate": "❓"
        }
        
        # Header
        md.append("# Compliance Matrix Report")
        md.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append("")
        
        # Matrix table
        md.append("## Compliance Matrix")
        md.append("")
        
        # Create header row with requirement IDs
        header = ["Document ID", "Document Name"]
        header.extend([f"{req['id']}" for req in requirements])
        
        # Add the header
        md.append("| " + " | ".join(header) + " |")
        md.append("| " + " | ".join(["---"] * len(header)) + " |")
        
        # Generate rows for each document
        for doc in documents:
            doc_id = doc["id"]
            doc_name = doc.get("name", doc_id)
            
            row = [doc_id, doc_name]
            
            # Find this document's compliance matrix entry
            matrix_entry = next((entry for entry in compliance_matrix if entry["document_id"] == doc_id), None)
            
            if matrix_entry:
                # Add a cell for each requirement
                for req in requirements:
                    req_id = req["id"]
                    result = matrix_entry["results"].get(req_id, {"compliance_level": "indeterminate"})
                    
                    # Get the compliance level
                    level = result.get("compliance_level", "indeterminate")
                    
                    # Format the cell based on visualization style
                    symbol = level_symbols.get(level, "❓")
                    
                    if self.include_confidence and "confidence_score" in result:
                        confidence = result["confidence_score"]
                        cell = f"{symbol} {confidence:.2f}"
                    else:
                        cell = symbol
                    
                    row.append(cell)
            else:
                # If no results for this document, add empty cells
                row.extend([""] * len(requirements))
            
            md.append("| " + " | ".join(row) + " |")
        
        # Add a section break
        md.append("")
        
        # Summary section
        md.append("## Summary")
        md.append("")
        
        summary = self._generate_matrix_summary(documents, requirements, compliance_matrix)
        overall_level = summary.get("overall_compliance", "indeterminate")
        overall_symbol = level_symbols.get(overall_level, "❓")
        
        md.append(f"**Overall Compliance:** {overall_symbol} {overall_level.replace('_', ' ').title()}")
        md.append("")
        
        # Add counts and percentages
        md.append("| Compliance Level | Count | Percentage |")
        md.append("| --- | --- | --- |")
        
        for level, count in summary.get("compliance_counts", {}).items():
            percentage = summary.get("compliance_percentages", {}).get(level, 0)
            symbol = level_symbols.get(level, "❓")
            
            md.append(f"| {symbol} {level.replace('_', ' ').title()} | {count} | {percentage:.1f}% |")
        
        return "\n".join(md)
    
    def _format_summary_markdown(self, data):
        """Format a summary report as Markdown"""
        md = []
        
        # Status to symbol mapping for markdown
        status_symbols = {
            "passed": "✅",
            "partial": "⚠️",
            "failed": "❌",
            "unknown": "❓",
            "error": "⛔",
            "fully_compliant": "✅",
            "partially_compliant": "⚠️",
            "non_compliant": "❌",
            "not_applicable": "➖",
            "indeterminate": "❓"
        }
        
        if isinstance(data, ValidationResult):
            # Generate summary from validation result
            status_counts = {"passed": 0, "partial": 0, "failed": 0, "unknown": 0, "error": 0}
            
            # Count statuses across categories
            for category in data.categories:
                for item in category.items:
                    status_counts[item.status] += 1
            
            # Header
            md.append(f"# Compliance Summary: {data.document_name}")
            md.append(f"Generated: {datetime.datetime.fromtimestamp(data.metadata.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            md.append("")
            
            # Document information
            md.append("## Document Information")
            md.append("")
            md.append(f"**Document ID:** {data.document_id}")
            md.append(f"**Document Type:** {data.document_type}")
            
            status = data.status
            status_symbol = status_symbols.get(status, "❓")
            md.append(f"**Overall Status:** {status_symbol} {status.upper()}")
            md.append(f"**Confidence:** {data.metadata.confidence_score:.2f}")
            md.append(f"**Mode:** {data.metadata.mode}")
            md.append("")
            
            # Status counts
            md.append("## Status Distribution")
            md.append("")
            md.append("| Status | Count | Percentage |")
            md.append("| --- | --- | --- |")
            
            total_items = sum(status_counts.values())
            for status, count in status_counts.items():
                if count > 0:
                    if total_items > 0:
                        percentage = (count / total_items) * 100
                    else:
                        percentage = 0
                    
                    status_symbol = status_symbols.get(status, "❓")
                    md.append(f"| {status_symbol} {status.upper()} | {count} | {percentage:.1f}% |")
            
            md.append("")
            
            # Category summary
            md.append("## Category Breakdown")
            md.append("")
            md.append("| Category | Status | Items | Passed | Partial | Failed | Other |")
            md.append("| --- | --- | --- | --- | --- | --- | --- |")
            
            for category in data.categories:
                cat_statuses = {"passed": 0, "partial": 0, "failed": 0, "unknown": 0, "error": 0}
                
                for item in category.items:
                    cat_statuses[item.status] += 1
                
                other_count = cat_statuses["unknown"] + cat_statuses["error"]
                
                status_symbol = status_symbols.get(category.status, "❓")
                md.append(
                    f"| {category.name} | {status_symbol} {category.status.upper()} | " +
                    f"{len(category.items)} | {cat_statuses['passed']} | " +
                    f"{cat_statuses['partial']} | {cat_statuses['failed']} | {other_count} |"
                )
            
        else:
            # Summary for matrix data
            summary = self._format_summary_json(data) if isinstance(data, dict) else data
            
            # Header
            md.append("# Compliance Matrix Summary")
            md.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            md.append("")
            
            # Overall compliance
            overall = summary.get("overall_compliance", "indeterminate")
            overall_symbol = status_symbols.get(overall, "❓")
            md.append(f"**Overall Compliance:** {overall_symbol} {overall.replace('_', ' ').title()}")
            md.append("")
            
            # Document summary
            md.append("## Document Summary")
            md.append("")
            md.append("| Document ID | Document Type | Status | Confidence |")
            md.append("| --- | --- | --- | --- |")
            
            for doc in summary.get("document_summary", []):
                status = doc.get("status", "unknown").lower()
                status_symbol = status_symbols.get(status, "❓")
                
                md.append(
                    f"| {doc['id']} | {doc.get('type', '')} | " +
                    f"{status_symbol} {status.upper()} | {doc.get('confidence', 0):.2f} |"
                )
            
            md.append("")
            
            # Requirement summary
            md.append("## Requirement Summary")
            md.append("")
            md.append("| Requirement ID | Category | Type | Priority | Compliance |")
            md.append("| --- | --- | --- | --- | --- |")
            
            for req in summary.get("requirement_summary", []):
                compliance = req.get("compliance", "unknown").lower()
                compliance_symbol = status_symbols.get(compliance, "❓")
                
                md.append(
                    f"| {req['id']} | {req.get('category', '')} | " +
                    f"{req.get('type', '')} | {req.get('priority', '')} | " +
                    f"{compliance_symbol} {compliance.replace('_', ' ').upper()} |"
                )
        
        return "\n".join(md)
    
    # === Helper methods ===
    
    def _save_json(self, data, output_path):
        """Save JSON data to a file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def _save_text(self, content, output_path):
        """Save text content to a file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _get_symbol_for_level(self, level):
        """Get the appropriate symbol for a compliance level"""
        if level == "fully_compliant":
            return "✓"
        elif level == "partially_compliant":
            return "⚠"
        elif level == "non_compliant":
            return "✗"
        elif level == "not_applicable":
            return "-"
        else:  # indeterminate or unknown
            return "?"
    
    def _generate_matrix_summary(self, documents, requirements, compliance_matrix):
        """Generate summary statistics for a compliance matrix"""
        # Count occurrences of each compliance level
        compliance_counts = {
            "fully_compliant": 0,
            "partially_compliant": 0,
            "non_compliant": 0,
            "not_applicable": 0,
            "indeterminate": 0
        }
        
        # Count total results
        total_results = 0
        
        # Process all matrix entries
        for entry in compliance_matrix:
            for req_id, result in entry.get("results", {}).items():
                level = result.get("compliance_level", "indeterminate")
                compliance_counts[level] += 1
                total_results += 1
        
        # Calculate percentages
        compliance_percentages = {}
        for level, count in compliance_counts.items():
            if total_results > 0:
                compliance_percentages[level] = (count / total_results) * 100
            else:
                compliance_percentages[level] = 0
        
        # Determine overall compliance
        if total_results > 0:
            fully_compliant_pct = compliance_percentages["fully_compliant"]
            partially_compliant_pct = compliance_percentages["partially_compliant"]
            
            if fully_compliant_pct >= 80:
                overall_compliance = "fully_compliant"
            elif fully_compliant_pct + partially_compliant_pct >= 60:
                overall_compliance = "partially_compliant"
            else:
                overall_compliance = "non_compliant"
        else:
            # No results to evaluate
            overall_compliance = "indeterminate"
        
        return {
            "overall_compliance": overall_compliance,
            "compliance_counts": compliance_counts,
            "compliance_percentages": compliance_percentages,
            "total_results": total_results
        }
    
    def _calculate_overall_compliance(self, data):
        """Calculate overall compliance level from matrix data"""
        if "summary" in data and "overall_compliance" in data["summary"]:
            return data["summary"]["overall_compliance"]["level"]
        
        # Otherwise, do a simple calculation based on matrix entries
        if "compliance_matrix" in data:
            fully = 0
            partial = 0
            non = 0
            total = 0
            
            for entry in data["compliance_matrix"]:
                for req_id, result in entry.get("results", {}).items():
                    level = result.get("compliance_level", "indeterminate")
                    if level == "fully_compliant":
                        fully += 1
                    elif level == "partially_compliant":
                        partial += 1
                    elif level == "non_compliant":
                        non += 1
                    total += 1
            
            if total > 0:
                fully_pct = (fully / total) * 100
                partial_pct = (partial / total) * 100
                
                if fully_pct >= 80:
                    return "fully_compliant"
                elif fully_pct + partial_pct >= 60:
                    return "partially_compliant"
                else:
                    return "non_compliant"
            
        return "indeterminate"
    
    def _summarize_documents(self, documents):
        """Create a summary of documents"""
        return [
            {
                "id": doc["id"],
                "name": doc.get("name", doc["id"]),
                "type": doc.get("type", "unknown"),
                "status": doc.get("status", "unknown"),
                "confidence": doc.get("confidence", 0.0)
            }
            for doc in documents
        ]
    
    def _summarize_requirements(self, requirements):
        """Create a summary of requirements"""
        return [
            {
                "id": req["id"],
                "description": req.get("description", ""),
                "category": req.get("category", ""),
                "type": req.get("type", ""),
                "priority": req.get("priority", ""),
                "compliance": req.get("compliance", "unknown")
            }
            for req in requirements
        ]

# === Test functions to generate evidence ===

def generate_sample_validation_result():
    """Generate a sample validation result for testing"""
    # Create metadata
    metadata = ValidationMetadata(
        timestamp=datetime.datetime.now().timestamp(),
        validator_version="1.0.0",
        mode="static",
        confidence_score=0.92,
        processing_time_ms=250.0,
        warnings=["This is a simulated validation result"]
    )
    
    # Create sample items for access control
    access_items = [
        ValidationItem(
            id="ACC001",
            name="Password Policy",
            status=ValidationStatus.PASSED,
            confidence_score=0.95,
            details={
                "justification": "Password policy meets all requirements with secure settings",
                "matched_keywords": ["password", "policy", "complexity", "requirements"]
            }
        ),
        ValidationItem(
            id="ACC002",
            name="Two-Factor Authentication",
            status=ValidationStatus.FAILED,
            confidence_score=0.90,
            details={
                "justification": "Two-factor authentication is not implemented for all systems",
                "matched_keywords": [],
                "missing_keywords": ["two-factor", "2fa", "mfa"]
            },
            errors=["Critical security feature missing"]
        ),
        ValidationItem(
            id="ACC003",
            name="Account Lockout",
            status=ValidationStatus.PARTIAL,
            confidence_score=0.85,
            details={
                "justification": "Account lockout implemented but threshold too high (10 attempts)",
                "matched_keywords": ["account", "lockout"],
                "missing_keywords": ["threshold"]
            },
            warnings=["Lockout threshold should be lowered"]
        )
    ]
    
    # Create sample items for data protection
    data_items = [
        ValidationItem(
            id="DAT001",
            name="Data Encryption at Rest",
            status=ValidationStatus.PASSED,
            confidence_score=0.92,
            details={
                "justification": "All sensitive data is encrypted at rest with AES-256",
                "matched_keywords": ["encryption", "at rest", "AES-256"]
            }
        ),
        ValidationItem(
            id="DAT002",
            name="Data Encryption in Transit",
            status=ValidationStatus.PASSED,
            confidence_score=0.95,
            details={
                "justification": "All data in transit is encrypted with TLS 1.2+",
                "matched_keywords": ["encryption", "transit", "TLS"]
            }
        ),
        ValidationItem(
            id="DAT003",
            name="Data Retention Policy",
            status=ValidationStatus.PARTIAL,
            confidence_score=0.80,
            details={
                "justification": "Data retention policy exists but lacks specific timeframes",
                "matched_keywords": ["retention", "policy"],
                "missing_keywords": ["timeframes", "deletion"]
            },
            warnings=["Policy needs more specific retention periods"]
        )
    ]
    
    # Create sample items for incident response
    incident_items = [
        ValidationItem(
            id="INC001",
            name="Incident Response Plan",
            status=ValidationStatus.PARTIAL,
            confidence_score=0.75,
            details={
                "justification": "Basic incident response plan exists but lacks detailed procedures",
                "matched_keywords": ["incident", "response", "plan"],
                "missing_keywords": ["procedures", "roles", "communication"]
            },
            warnings=["Plan needs more detail on procedures and roles"]
        ),
        ValidationItem(
            id="INC002",
            name="Security Event Monitoring",
            status=ValidationStatus.FAILED,
            confidence_score=0.88,
            details={
                "justification": "No centralized security event monitoring system in place",
                "matched_keywords": [],
                "missing_keywords": ["monitoring", "SIEM", "logs", "events"]
            },
            errors=["Critical monitoring system missing"]
        )
    ]
    
    # Create categories
    categories = [
        ValidationCategory(
            id="ACCESS",
            name="Access Control",
            status=ValidationStatus.PARTIAL,
            confidence_score=0.90,
            items=access_items,
            warnings=["Two-factor authentication needs implementation"]
        ),
        ValidationCategory(
            id="DATA",
            name="Data Protection",
            status=ValidationStatus.PASSED,
            confidence_score=0.89,
            items=data_items
        ),
        ValidationCategory(
            id="INCIDENT",
            name="Incident Response",
            status=ValidationStatus.FAILED,
            confidence_score=0.82,
            items=incident_items,
            errors=["Security monitoring implementation required"]
        )
    ]
    
    # Create validation result
    return ValidationResult(
        document_id="DOC-001",
        document_name="Security Policy.pdf",
        document_type="policy",
        status=ValidationStatus.PARTIAL,
        metadata=metadata,
        categories=categories,
        warnings=["Document has several compliance gaps that need addressing"]
    )

def generate_sample_matrix_data():
    """Generate sample matrix data for testing"""
    # Create sample documents
    documents = [
        {
            "id": "DOC-001",
            "name": "Security Policy.pdf",
            "type": "policy"
        },
        {
            "id": "DOC-002",
            "name": "Disaster Recovery Plan.pdf",
            "type": "procedure"
        },
        {
            "id": "DOC-003",
            "name": "Access Control Standard.pdf",
            "type": "standard"
        }
    ]
    
    # Create sample requirements
    requirements = [
        {
            "id": "REQ001",
            "description": "Password Policy",
            "category": "Access Control",
            "type": "mandatory",
            "priority": "high"
        },
        {
            "id": "REQ002",
            "description": "Two-Factor Authentication",
            "category": "Access Control",
            "type": "mandatory",
            "priority": "critical"
        },
        {
            "id": "REQ003",
            "description": "Data Encryption",
            "category": "Data Protection",
            "type": "mandatory",
            "priority": "critical"
        },
        {
            "id": "REQ004",
            "description": "Incident Response Plan",
            "category": "Incident Response",
            "type": "mandatory",
            "priority": "high"
        },
        {
            "id": "REQ005",
            "description": "Security Monitoring",
            "category": "Incident Response",
            "type": "mandatory",
            "priority": "high"
        }
    ]
    
    # Create sample compliance matrix
    compliance_matrix = [
        {
            "document_id": "DOC-001",
            "results": {
                "REQ001": {
                    "compliance_level": "fully_compliant",
                    "confidence_score": 0.95,
                    "justification": "Password policy fully documented and compliant"
                },
                "REQ002": {
                    "compliance_level": "non_compliant",
                    "confidence_score": 0.90,
                    "justification": "Two-factor authentication not implemented"
                },
                "REQ003": {
                    "compliance_level": "fully_compliant",
                    "confidence_score": 0.92,
                    "justification": "Data encryption requirements fully met"
                },
                "REQ004": {
                    "compliance_level": "partially_compliant",
                    "confidence_score": 0.75,
                    "justification": "Basic incident response coverage but incomplete"
                },
                "REQ005": {
                    "compliance_level": "non_compliant",
                    "confidence_score": 0.88,
                    "justification": "No security monitoring coverage"
                }
            }
        },
        {
            "document_id": "DOC-002",
            "results": {
                "REQ001": {
                    "compliance_level": "not_applicable",
                    "confidence_score": 0.95,
                    "justification": "Password policy not relevant to disaster recovery"
                },
                "REQ002": {
                    "compliance_level": "not_applicable",
                    "confidence_score": 0.95,
                    "justification": "Two-factor authentication not relevant to disaster recovery"
                },
                "REQ003": {
                    "compliance_level": "partially_compliant",
                    "confidence_score": 0.85,
                    "justification": "Some encryption requirements addressed in recovery process"
                },
                "REQ004": {
                    "compliance_level": "fully_compliant",
                    "confidence_score": 0.92,
                    "justification": "Incident response fully integrated with disaster recovery"
                },
                "REQ005": {
                    "compliance_level": "partially_compliant",
                    "confidence_score": 0.80,
                    "justification": "Some monitoring addressed but not comprehensive"
                }
            }
        },
        {
            "document_id": "DOC-003",
            "results": {
                "REQ001": {
                    "compliance_level": "fully_compliant",
                    "confidence_score": 0.98,
                    "justification": "Comprehensive password policy standards"
                },
                "REQ002": {
                    "compliance_level": "fully_compliant",
                    "confidence_score": 0.95,
                    "justification": "Detailed two-factor authentication standards"
                },
                "REQ003": {
                    "compliance_level": "partially_compliant",
                    "confidence_score": 0.75,
                    "justification": "Some encryption standards covered"
                },
                "REQ004": {
                    "compliance_level": "not_applicable",
                    "confidence_score": 0.90,
                    "justification": "Incident response not relevant to access control standard"
                },
                "REQ005": {
                    "compliance_level": "not_applicable",
                    "confidence_score": 0.90,
                    "justification": "Security monitoring not relevant to access control standard"
                }
            }
        }
    ]
    
    return documents, requirements, compliance_matrix

def run_tests():
    """Run tests and generate output examples in all formats"""
    print("=== OUTPUT FORMATTER DEMONSTRATION ===")
    print("Running standalone tests without dependencies")
    
    # Create output directory
    output_dir = Path("output_formatter_evidence")
    output_dir.mkdir(exist_ok=True)
    
    # Create a formatter
    formatter = OutputFormatter()
    
    # Generate sample data
    result = generate_sample_validation_result()
    documents, requirements, compliance_matrix = generate_sample_matrix_data()
    
    # Dictionary to track generated files
    generated_files = []
    
    print("\nGenerating document outputs...")
    for fmt in OutputFormat:
        try:
            # Create output path
            output_path = output_dir / f"document_{fmt.value}.{fmt.value}"
            
            # Generate the output
            print(f"  Generating {fmt.value} document report...")
            formatter.format_document(
                result=result,
                output_format=fmt,
                output_path=output_path
            )
            
            # Verify file was created
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"    ✓ Successfully created {output_path.name} ({file_size} bytes)")
                generated_files.append(str(output_path))
            else:
                print(f"    ✗ Failed to create {output_path.name}")
        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
    
    print("\nGenerating matrix outputs...")
    for fmt in OutputFormat:
        try:
            # Create output path
            output_path = output_dir / f"matrix_{fmt.value}.{fmt.value}"
            
            # Generate the output
            print(f"  Generating {fmt.value} matrix report...")
            formatter.format_matrix(
                documents=documents,
                requirements=requirements,
                compliance_matrix=compliance_matrix,
                output_format=fmt,
                output_path=output_path
            )
            
            # Verify file was created
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"    ✓ Successfully created {output_path.name} ({file_size} bytes)")
                generated_files.append(str(output_path))
            else:
                print(f"    ✗ Failed to create {output_path.name}")
        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
    
    print("\nGenerating summary outputs...")
    for fmt in OutputFormat:
        try:
            # Create output path
            output_path = output_dir / f"summary_{fmt.value}.{fmt.value}"
            
            # Generate the output
            print(f"  Generating {fmt.value} summary report...")
            formatter.format_summary(
                data=result,
                output_format=fmt,
                output_path=output_path
            )
            
            # Verify file was created
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"    ✓ Successfully created {output_path.name} ({file_size} bytes)")
                generated_files.append(str(output_path))
            else:
                print(f"    ✗ Failed to create {output_path.name}")
        except Exception as e:
            print(f"    ✗ Error: {str(e)}")
    
    # Create evidence summary
    evidence_summary = {
        "test_timestamp": datetime.datetime.now().isoformat(),
        "output_formatter_version": "1.0.0",
        "evidence_directory": str(output_dir.absolute()),
        "generated_files": generated_files,
        "formats_tested": [fmt.value for fmt in OutputFormat],
        "total_files_generated": len(generated_files)
    }
    
    # Save evidence summary
    with open(output_dir / "evidence_summary.json", "w", encoding="utf-8") as f:
        json.dump(evidence_summary, f, indent=2)
    
    print(f"\nGenerated {len(generated_files)} output files in {len(OutputFormat)} formats")
    print(f"Evidence files available in: {output_dir.absolute()}")
    print("=== TEST EXECUTION COMPLETE ===")
    
    return 0

if __name__ == "__main__":
    sys.exit(run_tests())