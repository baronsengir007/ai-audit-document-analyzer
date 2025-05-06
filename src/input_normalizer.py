"""
Input Normalizer Module
Handles normalization and sanitization of input documents.
"""

import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path

from .interfaces import Document

class InputNormalizer:
    """Handles normalization and sanitization of input documents"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def normalize_document(self, document: Document) -> Document:
        """
        Normalize and sanitize a document
        
        Args:
            document: The document to normalize
            
        Returns:
            Normalized Document object
        """
        try:
            # Create normalized copy of document
            normalized = Document(
                filename=self._normalize_filename(document.filename),
                content=self._normalize_content(document.content),
                classification=document.classification,
                metadata=self._normalize_metadata(document.metadata),
                source_path=document.source_path
            )
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"Error normalizing document: {str(e)}")
            # Return original document if normalization fails
            return document
    
    def _normalize_filename(self, filename: str) -> str:
        """Normalize document filename"""
        # Remove invalid characters
        normalized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Ensure proper extension
        if not normalized.endswith(('.pdf', '.docx', '.xlsx')):
            normalized += '.pdf'  # Default to PDF if no extension
        
        return normalized
    
    def _normalize_content(self, content: str) -> str:
        """Normalize document content"""
        if not content:
            return ""
        
        # Remove control characters
        content = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', content)
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove excessive line breaks
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def _normalize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize document metadata"""
        if not metadata:
            return {}
        
        normalized = {}
        
        # Convert all keys to lowercase
        for key, value in metadata.items():
            normalized_key = key.lower().strip()
            
            # Handle different value types
            if isinstance(value, str):
                normalized[normalized_key] = value.strip()
            elif isinstance(value, (int, float, bool)):
                normalized[normalized_key] = value
            elif isinstance(value, list):
                normalized[normalized_key] = [str(v).strip() for v in value]
            elif isinstance(value, dict):
                normalized[normalized_key] = self._normalize_metadata(value)
            else:
                normalized[normalized_key] = str(value).strip()
        
        return normalized
    
    def validate_document(self, document: Document) -> Dict[str, Any]:
        """
        Validate a document and return validation results
        
        Args:
            document: The document to validate
            
        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            "is_valid": True,
            "issues": [],
            "normalization_required": False
        }
        
        # Check filename
        if not self._is_valid_filename(document.filename):
            validation_results["is_valid"] = False
            validation_results["issues"].append("Invalid filename")
            validation_results["normalization_required"] = True
        
        # Check content
        if not self._is_valid_content(document.content):
            validation_results["is_valid"] = False
            validation_results["issues"].append("Invalid content")
            validation_results["normalization_required"] = True
        
        # Check metadata
        if not self._is_valid_metadata(document.metadata):
            validation_results["is_valid"] = False
            validation_results["issues"].append("Invalid metadata")
            validation_results["normalization_required"] = True
        
        return validation_results
    
    def _is_valid_filename(self, filename: str) -> bool:
        """Check if filename is valid"""
        if not filename:
            return False
        
        # Check for invalid characters
        if re.search(r'[<>:"/\\|?*]', filename):
            return False
        
        # Check for valid extension
        if not filename.endswith(('.pdf', '.docx', '.xlsx')):
            return False
        
        return True
    
    def _is_valid_content(self, content: str) -> bool:
        """Check if content is valid"""
        if content is None:
            return False
        
        # Check for control characters
        if re.search(r'[\x00-\x1F\x7F-\x9F]', content):
            return False
        
        # Check for excessive whitespace
        if re.search(r'\s{3,}', content):
            return False
        
        return True
    
    def _is_valid_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Check if metadata is valid"""
        if metadata is None:
            return False
        
        # Check for invalid keys
        for key in metadata:
            if not isinstance(key, str) or not key.strip():
                return False
            
            # Check for invalid characters in keys
            if re.search(r'[<>:"/\\|?*]', key):
                return False
        
        return True 