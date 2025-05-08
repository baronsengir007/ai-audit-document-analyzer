"""
Type Verification Module
Verifies document types against required types and generates verification reports.
"""

import logging
import yaml
import json
from typing import Dict, List, Set, Any, Tuple, Optional
from pathlib import Path

class TypeVerification:
    """
    Verifies document types against a list of required types from configuration.
    Calculates coverage metrics and identifies missing and extra document types.
    """
    
    def __init__(
        self,
        config_path: str = "config/document_types.yaml",
        confidence_threshold: float = 0.7
    ):
        """
        Initialize the type verification.
        
        Args:
            config_path: Path to the document types configuration file
            confidence_threshold: Minimum confidence threshold for accepting a classification
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.confidence_threshold = confidence_threshold
        
        # Load document types configuration
        self.document_types = self._load_document_types()
        self.required_types = self._get_required_types()
        
        self.logger.info(f"Loaded {len(self.document_types)} document types, {len(self.required_types)} required")
    
    def _load_document_types(self) -> List[Dict[str, Any]]:
        """
        Load document types from the configuration file.
        
        Returns:
            List of document type configurations
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config or 'document_types' not in config:
                self.logger.error(f"Invalid or empty document types configuration: {self.config_path}")
                return []
                
            return config['document_types']
            
        except Exception as e:
            self.logger.error(f"Error loading document types configuration: {e}")
            return []
    
    def _get_required_types(self) -> List[Dict[str, Any]]:
        """
        Extract required document types from the configuration.
        
        Returns:
            List of required document type configurations
        """
        return [doc_type for doc_type in self.document_types if doc_type.get('required', False)]
    
    def verify_documents(self, classified_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify classified documents against required document types.
        
        Args:
            classified_documents: List of documents with classification results
            
        Returns:
            Dictionary with verification results containing:
            - found_types: List of found required document types
            - missing_types: List of missing required document types
            - extra_types: List of found document types that aren't required
            - coverage: Percentage of required types that were found
            - documents_by_type: Dictionary mapping type IDs to lists of document filenames
            - unclassified_documents: List of documents that couldn't be classified confidently
        """
        # Initialize result structure
        result = {
            "found_types": [],
            "missing_types": [],
            "extra_types": [],
            "coverage": 0.0,
            "documents_by_type": {},
            "unclassified_documents": []
        }
        
        # Track which required types have been found
        required_type_ids = {doc_type['id'] for doc_type in self.required_types}
        found_type_ids = set()
        extra_type_ids = set()
        
        # Group documents by classified type
        for doc in classified_documents:
            # Skip documents without classification results
            if 'classification_result' not in doc:
                self.logger.warning(f"Document has no classification result: {doc.get('filename', 'unknown')}")
                continue
            
            classification = doc['classification_result']
            type_id = classification.get('type_id', 'unknown')
            confidence = classification.get('confidence', 0.0)
            
            # Skip low-confidence classifications
            if confidence < self.confidence_threshold:
                result["unclassified_documents"].append({
                    "filename": doc.get('filename', 'unknown'),
                    "type_id": type_id,
                    "confidence": confidence
                })
                continue
            
            # Track found type
            if type_id in required_type_ids:
                found_type_ids.add(type_id)
            elif type_id != "unknown":
                extra_type_ids.add(type_id)
            
            # Add document to the appropriate type group
            if type_id not in result["documents_by_type"]:
                result["documents_by_type"][type_id] = []
            
            result["documents_by_type"][type_id].append({
                "filename": doc.get('filename', 'unknown'),
                "confidence": confidence
            })
        
        # Determine missing types
        missing_type_ids = required_type_ids - found_type_ids
        
        # Build detailed result
        for doc_type in self.document_types:
            type_id = doc_type['id']
            type_details = {
                "id": type_id,
                "name": doc_type['name'],
                "required": doc_type.get('required', False),
                "description": doc_type['description']
            }
            
            if type_id in found_type_ids:
                # Add documents count for this type
                type_details["document_count"] = len(result["documents_by_type"].get(type_id, []))
                result["found_types"].append(type_details)
            elif type_id in missing_type_ids:
                result["missing_types"].append(type_details)
            elif type_id in extra_type_ids:
                # Add documents count for this type
                type_details["document_count"] = len(result["documents_by_type"].get(type_id, []))
                result["extra_types"].append(type_details)
        
        # Add unknown type to extra types if present
        if "unknown" in result["documents_by_type"]:
            result["extra_types"].append({
                "id": "unknown",
                "name": "Unknown",
                "required": False,
                "description": "Documents that couldn't be classified into a known type",
                "document_count": len(result["documents_by_type"]["unknown"])
            })
        
        # Calculate coverage
        if len(required_type_ids) > 0:
            result["coverage"] = len(found_type_ids) / len(required_type_ids)
        
        # Add summary stats
        result["total_documents"] = len(classified_documents)
        result["total_required_types"] = len(required_type_ids)
        result["total_found_required_types"] = len(found_type_ids)
        result["total_missing_types"] = len(missing_type_ids)
        result["total_extra_types"] = len(extra_type_ids)
        result["unclassified_count"] = len(result["unclassified_documents"])
        result["confidence_threshold"] = self.confidence_threshold
        
        # Log verification results
        self.logger.info(
            f"Verification complete: {result['total_found_required_types']}/{result['total_required_types']} "
            f"required types found ({result['coverage']*100:.1f}% coverage)"
        )
        if result["total_missing_types"] > 0:
            self.logger.warning(f"Missing {result['total_missing_types']} required document types")
        
        return result
    
    def get_missing_types_summary(self, verification_result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of missing document types.
        
        Args:
            verification_result: Result from verify_documents method
            
        Returns:
            Human-readable summary of missing types
        """
        if not verification_result.get("missing_types"):
            return "All required document types are present."
        
        missing_types = verification_result["missing_types"]
        summary = [
            f"Missing {len(missing_types)} required document types:",
            ""
        ]
        
        for doc_type in missing_types:
            summary.append(f"- {doc_type['name']}: {doc_type['description']}")
        
        return "\n".join(summary)
    
    def generate_verification_report(
        self, 
        verification_result: Dict[str, Any],
        output_format: str = "text"
    ) -> str:
        """
        Generate a verification report in the specified format.
        
        Args:
            verification_result: Result from verify_documents method
            output_format: Format of the report ("text", "json", "markdown")
            
        Returns:
            Verification report in the specified format
        """
        if output_format == "json":
            return json.dumps(verification_result, indent=2)
        
        # Generate text/markdown report
        is_markdown = output_format == "markdown"
        
        # Helper for section headers
        def header(text, level=1):
            if is_markdown:
                prefix = "#" * level
                return f"{prefix} {text}\n\n"
            else:
                underline = "=" if level == 1 else "-"
                return f"{text}\n{underline * len(text)}\n\n"
        
        # Helper for lists
        def list_item(text):
            return f"{'* ' if is_markdown else '- '}{text}"
        
        report = []
        
        # Add report header
        report.append(header("Document Type Verification Report"))
        
        # Add summary section
        report.append(header("Summary", 2))
        report.append(f"Total documents: {verification_result['total_documents']}\n")
        report.append(f"Required types: {verification_result['total_required_types']}\n")
        report.append(f"Found required types: {verification_result['total_found_required_types']}\n")
        report.append(f"Missing required types: {verification_result['total_missing_types']}\n")
        report.append(f"Extra types: {verification_result['total_extra_types']}\n")
        report.append(f"Unclassified documents: {verification_result['unclassified_count']}\n")
        report.append(f"Coverage: {verification_result['coverage']*100:.1f}%\n")
        report.append(f"Confidence threshold: {verification_result['confidence_threshold']}\n\n")
        
        # Add found types section
        report.append(header("Found Required Document Types", 2))
        if verification_result["found_types"]:
            for doc_type in verification_result["found_types"]:
                report.append(list_item(f"{doc_type['name']} ({doc_type['document_count']} documents)"))
                report.append(f"   {doc_type['description']}\n")
        else:
            report.append("No required document types were found.\n\n")
        
        # Add missing types section
        report.append(header("Missing Required Document Types", 2))
        if verification_result["missing_types"]:
            for doc_type in verification_result["missing_types"]:
                report.append(list_item(f"{doc_type['name']}"))
                report.append(f"   {doc_type['description']}\n")
        else:
            report.append("All required document types are present.\n\n")
        
        # Add extra types section
        report.append(header("Extra Document Types", 2))
        if verification_result["extra_types"]:
            for doc_type in verification_result["extra_types"]:
                report.append(list_item(f"{doc_type['name']} ({doc_type['document_count']} documents)"))
                report.append(f"   {doc_type['description']}\n")
        else:
            report.append("No extra document types were found.\n\n")
        
        # Add unclassified documents section
        report.append(header("Unclassified Documents", 2))
        if verification_result["unclassified_documents"]:
            for doc in verification_result["unclassified_documents"]:
                report.append(list_item(f"{doc['filename']} (confidence: {doc['confidence']:.2f})"))
            report.append("\n")
        else:
            report.append("All documents were classified with confidence above threshold.\n\n")
        
        return "".join(report)


# Standalone function that uses the TypeVerification class
def verify_document_types(
    classified_documents: List[Dict[str, Any]],
    config_path: str = "config/document_types.yaml",
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Verify classified documents against required document types.
    
    Args:
        classified_documents: List of documents with classification results
        config_path: Path to document types configuration
        confidence_threshold: Minimum confidence threshold for accepting a classification
        
    Returns:
        Dictionary with verification results
    """
    verifier = TypeVerification(config_path=config_path, confidence_threshold=confidence_threshold)
    return verifier.verify_documents(classified_documents)