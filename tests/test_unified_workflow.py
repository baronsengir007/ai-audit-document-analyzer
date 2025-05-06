"""
Test suite for unified workflow functionality.
Tests document processing, mode selection, and edge case handling.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from src.unified_workflow_manager import UnifiedWorkflowManager
from src.interfaces import Document, ComplianceResult
from src.edge_case_handler import EdgeCaseType

class TestUnifiedWorkflow(unittest.TestCase):
    """Test suite for unified workflow functionality"""
    
    def setUp(self):
        """Set up before each test"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_files_dir = Path(self.temp_dir) / "test_files"
        self.test_files_dir.mkdir()
        
        # Initialize workflow manager with test configuration
        self.config = {
            "mode_preferences": {
                "policy": "dynamic",
                "report": "static"
            },
            "confidence_threshold": 0.7,
            "max_retries": 3
        }
        self.workflow = UnifiedWorkflowManager(config=self.config)
        
        # Create a test document
        self.test_doc = Document(
            filename="test_document.pdf",
            content="This is a test document content.",
            classification="test_type",
            metadata={"test": "metadata"}
        )
    
    def tearDown(self):
        """Clean up after each test"""
        shutil.rmtree(self.temp_dir)
    
    def test_process_document(self):
        """Test basic document processing"""
        result = self.workflow.process_document(self.test_doc)
        
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertEqual(result.confidence, 0.0)
        self.assertIn("normalized_document", result.details)
        self.assertEqual(result.mode_used, "test")
    
    def test_batch_processing(self):
        """Test batch processing"""
        docs = [
            Document(filename="doc1.pdf", content="content1", classification="test", metadata={}),
            Document(filename="doc2.pdf", content="content2", classification="test", metadata={})
        ]
        
        results = self.workflow.process_batch(docs)
        
        self.assertEqual(len(results), len(docs))
        for result in results:
            self.assertIsInstance(result, ComplianceResult)
            self.assertFalse(result.is_compliant)
    
    def test_save_results(self):
        """Test saving results"""
        results = [
            ComplianceResult(is_compliant=True, confidence=0.9, details={}, mode_used="test"),
            ComplianceResult(is_compliant=False, confidence=0.0, details={}, mode_used="test")
        ]
        
        output_path = Path(self.temp_dir) / "results.json"
        self.workflow.save_results(results, output_path)
        
        self.assertTrue(output_path.exists())
        with open(output_path, "r") as f:
            content = f.read()
            self.assertEqual(content, "test")

if __name__ == "__main__":
    unittest.main() 