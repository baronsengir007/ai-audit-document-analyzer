"""
Test suite for unified workflow functionality.
Tests document processing, mode selection, and edge case handling.
"""

import unittest
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

from .unified_workflow_manager import UnifiedWorkflowManager
from .interfaces import Document, ComplianceResult
from .edge_case_handler import EdgeCaseType

class TestUnifiedWorkflow(unittest.TestCase):
    """Test suite for unified workflow functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        cls.logger = logging.getLogger("test_unified_workflow")
        
        # Create temporary directory for test files
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_files_dir = Path(cls.temp_dir) / "test_files"
        cls.test_files_dir.mkdir()
        
        # Initialize workflow manager with test configuration
        cls.config = {
            "mode_preferences": {
                "policy": "dynamic",
                "report": "static"
            },
            "confidence_threshold": 0.7,
            "max_retries": 3
        }
        cls.workflow = UnifiedWorkflowManager(config=cls.config)
    
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
    
    def test_document_normalization(self):
        """Test document normalization"""
        # Create document with invalid characters
        doc = Document(
            filename="test<>.pdf",
            content="Test\n\n\ncontent",
            classification="test",
            metadata={"key": "value"}
        )
        
        # Process document
        result = self.workflow.process_document(doc)
        
        # Verify normalization
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertIn("normalized_document", result.details)
    
    def test_llm_extraction_failure(self):
        """Test handling of LLM extraction failures"""
        # Create document that would cause LLM failure
        doc = Document(
            filename="test.pdf",
            content="",  # Empty content would cause LLM failure
            classification="test",
            metadata={}
        )
        
        # Process document
        result = self.workflow.process_document(doc)
        
        # Verify error handling
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertIn("fallback_method", result.details)
    
    def test_unmatched_document(self):
        """Test handling of unmatched documents"""
        # Create document with unknown type
        doc = Document(
            filename="test.pdf",
            content="Unknown document type",
            classification="unknown",
            metadata={}
        )
        
        # Process document
        result = self.workflow.process_document(doc)
        
        # Verify handling
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertIn("method", result.details)
    
    def test_ambiguous_compliance(self):
        """Test handling of ambiguous compliance cases"""
        # Create document with conflicting indicators
        doc = Document(
            filename="test.pdf",
            content="This document both passes and fails requirements",
            classification="test",
            metadata={}
        )
        
        # Process document
        result = self.workflow.process_document(doc)
        
        # Verify handling
        self.assertIsInstance(result, ComplianceResult)
        self.assertIn("static_validation", result.details)
        self.assertIn("dynamic_validation", result.details)
    
    def test_corrupted_evaluation(self):
        """Test handling of corrupted evaluation results"""
        # Create document that would cause evaluation corruption
        doc = Document(
            filename="test.pdf",
            content="Invalid content that would corrupt evaluation",
            classification="test",
            metadata={}
        )
        
        # Process document
        result = self.workflow.process_document(doc)
        
        # Verify handling
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertIn("recovered_results", result.details)
    
    def test_unexpected_input(self):
        """Test handling of unexpected input"""
        # Create document with invalid content
        doc = Document(
            filename="test.pdf",
            content=None,  # Invalid content
            classification="test",
            metadata={}
        )
        
        # Process document
        result = self.workflow.process_document(doc)
        
        # Verify handling
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertIn("normalized_document", result.details)
    
    def test_batch_processing(self):
        """Test batch processing with edge cases"""
        # Create test documents
        docs = [
            Document(filename="valid.pdf", content="Valid content", classification="test", metadata={}),
            Document(filename="invalid.pdf", content=None, classification="test", metadata={}),
            Document(filename="unknown.pdf", content="Unknown type", classification="unknown", metadata={})
        ]
        
        # Process batch
        results = self.workflow.process_batch(docs)
        
        # Verify results
        self.assertEqual(len(results), len(docs))
        for result in results:
            self.assertIsInstance(result, ComplianceResult)
    
    def test_edge_case_statistics(self):
        """Test edge case statistics tracking"""
        # Process documents with various edge cases
        self.test_llm_extraction_failure()
        self.test_unmatched_document()
        self.test_ambiguous_compliance()
        
        # Get statistics
        stats = self.workflow.edge_case_handler.get_edge_case_stats()
        
        # Verify statistics
        self.assertGreater(stats["total_cases"], 0)
        self.assertIn(EdgeCaseType.LLM_EXTRACTION_FAILURE.value, stats["by_type"])
        self.assertIn(EdgeCaseType.UNMATCHED_DOCUMENT.value, stats["by_type"])
        self.assertIn(EdgeCaseType.AMBIGUOUS_COMPLIANCE.value, stats["by_type"])
    
    def test_save_results(self):
        """Test saving results with edge case information"""
        # Create test results
        results = [
            ComplianceResult(is_compliant=True, confidence=0.9, details={}, mode_used="static"),
            ComplianceResult(is_compliant=False, confidence=0.0, details={"error": "test"}, mode_used="error")
        ]
        
        # Save results
        output_path = Path(self.temp_dir) / "results.json"
        self.workflow.save_results(results, output_path)
        
        # Verify file was created
        self.assertTrue(output_path.exists())
        
        # Verify content
        with open(output_path, "r") as f:
            content = f.read()
            self.assertIn("test", content)

if __name__ == "__main__":
    unittest.main() 