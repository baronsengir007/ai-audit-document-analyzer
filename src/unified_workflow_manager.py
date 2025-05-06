"""
Unified Workflow Manager
Manages the unified workflow combining static and dynamic compliance checks.
"""

from typing import Dict, List, Optional, Any, Union
import logging
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor
import json
import yaml

from .interfaces import Document, ComplianceResult
from .edge_case_handler import EdgeCaseHandler, EdgeCaseType
from .static_mode_adapter import StaticModeAdapter
from .dynamic_mode_adapter import DynamicModeAdapter
from .document_classifier import DocumentClassifier

class UnifiedWorkflowManager:
    """Manages the unified workflow combining static and dynamic compliance checks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[Union[str, Path]] = None):
        self.logger = logging.getLogger(__name__)
        
        # Load configuration from file if config_path is provided
        if config_path:
            try:
                config_path = Path(config_path) if not isinstance(config_path, Path) else config_path
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        self.config = yaml.safe_load(f) or {}
                        self.logger.info(f"Loaded configuration from {config_path}")
                else:
                    self.logger.warning(f"Configuration file not found: {config_path}, using defaults")
                    self.config = config or {}
            except Exception as e:
                self.logger.error(f"Error loading configuration from {config_path}: {e}")
                self.config = config or {}
        else:
            self.config = config or {}
        
        # Initialize components
        self.edge_case_handler = EdgeCaseHandler()
        self.document_classifier = DocumentClassifier()
        self.static_mode = StaticModeAdapter()
        self.dynamic_mode = DynamicModeAdapter()
        
        # Set default configuration
        self.mode_preferences = self.config.get("mode_preferences", {
            "policy": "dynamic",
            "report": "static"
        })
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.max_retries = self.config.get("max_retries", 3)
        self.timeout_seconds = self.config.get("timeout_seconds", 300)
    
    def process_document(self, document: Document) -> ComplianceResult:
        """
        Process a document using the unified workflow.
        
        Args:
            document: Document to process
            
        Returns:
            ComplianceResult containing processing results
        """
        try:
            # Classify document
            doc_type = self.document_classifier.classify(document)
            is_complex = self.document_classifier.is_complex(document)
            
            # Determine processing mode
            mode = self._determine_processing_mode(doc_type, is_complex)
            
            # Process document
            start_time = time.time()
            result = self._process_with_mode(document, mode)
            
            # Check for timeouts
            if time.time() - start_time > self.timeout_seconds:
                self.edge_case_handler.handle_edge_case(
                    EdgeCaseType.TIMEOUT,
                    document.filename,
                    {"processing_time": time.time() - start_time},
                    "fallback"
                )
                result = self._process_with_mode(document, "static")  # Fallback to static mode
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing document {document.filename}: {str(e)}")
            
            # Handle edge case
            self.edge_case_handler.handle_edge_case(
                EdgeCaseType.UNEXPECTED_INPUT,
                document.filename,
                {"error": str(e)},
                "manual_review"
            )
            
            return ComplianceResult(
                is_compliant=False,
                confidence=0.0,
                details={"error": str(e)},
                mode_used="error"
            )
    
    def _determine_processing_mode(self, doc_type: str, is_complex: bool) -> str:
        """
        Determine the appropriate processing mode based on document type and complexity
        
        Args:
            doc_type: Document type
            is_complex: Whether the document is complex
            
        Returns:
            Processing mode to use
        """
        # Use dynamic mode for complex documents or policy documents
        if is_complex or doc_type == "policy":
            return "dynamic"
        
        # Use static mode for simple reports
        if doc_type == "report":
            return "static"
        
        # Default to static mode
        return "static"
    
    def _process_with_mode(self, document: Document, mode: str) -> ComplianceResult:
        """
        Process a document with the specified mode
        
        Args:
            document: Document to process
            mode: Processing mode to use
            
        Returns:
            ComplianceResult containing processing results
        """
        if mode == "static":
            return self.static_mode.process(document)
        else:
            return self.dynamic_mode.process(document)
    
    def process_batch(self, documents: List[Document]) -> List[ComplianceResult]:
        """
        Process a batch of documents
        
        Args:
            documents: List of documents to process
            
        Returns:
            List of ComplianceResult objects
        """
        results = []
        with ThreadPoolExecutor(max_workers=self.config.get("max_workers", 4)) as executor:
            futures = [executor.submit(self.process_document, doc) for doc in documents]
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error in batch processing: {str(e)}")
                    results.append(ComplianceResult(
                        is_compliant=False,
                        confidence=0.0,
                        details={"error": str(e)},
                        mode_used="error"
                    ))
        return results
    
    def save_results(self, results: List[ComplianceResult], output_path: Path) -> None:
        """
        Save processing results to a file
        
        Args:
            results: List of ComplianceResult objects
            output_path: Path to save results to
        """
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert results to JSON-serializable format
        results_data = []
        for result in results:
            result_dict = {
                "is_compliant": result.is_compliant,
                "confidence": result.confidence,
                "details": result.details,
                "mode_used": result.mode_used
            }
            results_data.append(result_dict)
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        self.logger.info(f"Saved {len(results)} results to {output_path}") 