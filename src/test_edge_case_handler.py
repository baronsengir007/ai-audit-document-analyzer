"""
Test suite for edge case handling functionality.
Tests various edge cases and their handling mechanisms.
"""

import unittest
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

from .edge_case_handler import EdgeCaseHandler, EdgeCaseType
from .interfaces import Document, ComplianceResult

class TestEdgeCaseHandler(unittest.TestCase):
    """Test suite for edge case handling functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        cls.logger = logging.getLogger("test_edge_case_handler")
        
        # Create temporary directory for edge case logs
        cls.temp_dir = tempfile.mkdtemp()
        cls.edge_cases_dir = Path(cls.temp_dir) / "logs" / "edge_cases"
        cls.edge_cases_dir.mkdir(parents=True)
        
        # Initialize edge case handler
        cls.handler = EdgeCaseHandler(logger=cls.logger)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """Set up before each test"""
        # Create a test document
        self.test_doc = Document(
            filename="test_document.pdf",
            content="This is a test document content.",
            classification="test_type",
            metadata={"test": "metadata"}
        )
    
    def test_handle_llm_extraction_failure(self):
        """Test handling of LLM extraction failures"""
        # Create a mock error
        error = Exception("LLM extraction failed")
        
        # Handle the error
        result = self.handler.handle_llm_extraction_failure(self.test_doc, error)
        
        # Verify result
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertLess(result.confidence, 1.0)
        self.assertIn("fallback_method", result.details)
    
    def test_handle_unmatched_document(self):
        """Test handling of unmatched documents"""
        # Handle unmatched document
        result = self.handler.handle_unmatched_document(self.test_doc)
        
        # Verify result
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertLess(result.confidence, 1.0)
        self.assertIn("method", result.details)
    
    def test_handle_ambiguous_compliance(self):
        """Test handling of ambiguous compliance cases"""
        # Create initial result
        initial_result = ComplianceResult(
            is_compliant=True,
            confidence=0.5,
            details={"initial": "result"}
        )
        
        # Handle ambiguous case
        result = self.handler.handle_ambiguous_compliance(self.test_doc, initial_result)
        
        # Verify result
        self.assertIsInstance(result, ComplianceResult)
        self.assertTrue(result.is_compliant)  # Should keep initial determination
        self.assertGreater(result.confidence, 0.0)
        self.assertIn("static_validation", result.details)
        self.assertIn("dynamic_validation", result.details)
    
    def test_handle_corrupted_evaluation(self):
        """Test handling of corrupted evaluation results"""
        # Create a mock error
        error = Exception("Evaluation corrupted")
        
        # Handle corrupted evaluation
        result = self.handler.handle_corrupted_evaluation(self.test_doc, error)
        
        # Verify result
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertLess(result.confidence, 1.0)
        self.assertIn("recovered_results", result.details)
    
    def test_handle_unexpected_input(self):
        """Test handling of unexpected input"""
        # Handle unexpected input
        result = self.handler.handle_unexpected_input(self.test_doc)
        
        # Verify result
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertLess(result.confidence, 1.0)
        self.assertIn("normalized_document", result.details)
    
    def test_edge_case_logging(self):
        """Test edge case logging functionality"""
        # Trigger an edge case
        self.handler._log_edge_case(EdgeCaseType.LLM_EXTRACTION_FAILURE, self.test_doc)
        
        # Verify edge case was logged
        stats = self.handler.get_edge_case_stats()
        self.assertGreater(stats["total_cases"], 0)
        self.assertGreater(stats["by_type"][EdgeCaseType.LLM_EXTRACTION_FAILURE.value], 0)
    
    def test_edge_case_saving(self):
        """Test saving edge case information"""
        # Create an edge case
        edge_case = EdgeCaseType.LLM_EXTRACTION_FAILURE
        self.handler._log_edge_case(edge_case, self.test_doc)
        
        # Verify edge case was saved
        case_files = list(self.edge_cases_dir.glob("*.json"))
        self.assertGreater(len(case_files), 0)
        
        # Verify file content
        with open(case_files[0], "r") as f:
            content = f.read()
            self.assertIn("LLM_EXTRACTION_FAILURE", content)
            self.assertIn(self.test_doc.filename, content)
    
    def test_error_handling(self):
        """Test error handling in edge case processing"""
        # Create a document with invalid content
        invalid_doc = Document(
            filename="invalid.pdf",
            content=None,  # Invalid content
            classification="test_type",
            metadata={}
        )
        
        # Try to handle various edge cases with invalid document
        with self.assertLogs(level="ERROR"):
            self.handler.handle_llm_extraction_failure(invalid_doc, Exception("test"))
            self.handler.handle_unmatched_document(invalid_doc)
            self.handler.handle_unexpected_input(invalid_doc)

if __name__ == "__main__":
    unittest.main() 