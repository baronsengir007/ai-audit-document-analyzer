"""
Validation Result Recovery Module
Handles recovery of partial or corrupted validation results.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import re

from .interfaces import Document

class ValidationResultRecovery:
    """Handles recovery of partial or corrupted validation results"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def recover_partial_results(self, document: Document) -> Optional[Dict[str, Any]]:
        """
        Attempt to recover partial validation results from a document
        
        Args:
            document: The document to recover results from
            
        Returns:
            Dictionary containing recovered results, or None if recovery failed
        """
        try:
            # Try to extract any existing validation markers
            markers = self._extract_validation_markers(document.content)
            if markers:
                return {
                    "recovered_markers": markers,
                    "recovery_method": "marker_extraction"
                }
            
            # Try to find partial results in document metadata
            if document.metadata:
                partial_results = self._extract_from_metadata(document.metadata)
                if partial_results:
                    return {
                        "recovered_results": partial_results,
                        "recovery_method": "metadata_extraction"
                    }
            
            # Try to find cached results
            cached_results = self._check_cached_results(document)
            if cached_results:
                return {
                    "recovered_results": cached_results,
                    "recovery_method": "cache_retrieval"
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error recovering partial results: {str(e)}")
            return None
    
    def _extract_validation_markers(self, content: str) -> List[Dict[str, Any]]:
        """Extract validation markers from document content"""
        markers = []
        
        # Look for common validation marker patterns
        patterns = [
            r"\[VALIDATION:([^\]]+)\]",  # [VALIDATION:type=pass]
            r"\{VALIDATION:([^\}]+)\}",  # {VALIDATION:type=pass}
            r"<!--VALIDATION:([^>]+)-->",  # <!--VALIDATION:type=pass-->
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                try:
                    marker_text = match.group(1)
                    # Parse marker text into key-value pairs
                    marker_data = {}
                    for pair in marker_text.split(","):
                        if "=" in pair:
                            key, value = pair.split("=", 1)
                            marker_data[key.strip()] = value.strip()
                    
                    if marker_data:
                        markers.append({
                            "type": "marker",
                            "data": marker_data,
                            "position": match.start()
                        })
                except Exception as e:
                    self.logger.warning(f"Error parsing validation marker: {str(e)}")
                    continue
        
        return markers
    
    def _extract_from_metadata(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract partial results from document metadata"""
        # Look for validation-related metadata
        validation_keys = [
            "validation_status",
            "compliance_status",
            "validation_results",
            "compliance_results"
        ]
        
        for key in validation_keys:
            if key in metadata:
                return {
                    "source": "metadata",
                    "key": key,
                    "value": metadata[key]
                }
        
        return None
    
    def _check_cached_results(self, document: Document) -> Optional[Dict[str, Any]]:
        """Check for cached validation results"""
        try:
            cache_dir = Path("cache/validation_results")
            if not cache_dir.exists():
                return None
            
            # Look for cached results for this document
            cache_file = cache_dir / f"{document.filename}.json"
            if cache_file.exists():
                with open(cache_file, "r") as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking cached results: {str(e)}")
            return None 