"""
Test suite for edge case handling functionality.
Tests edge case detection, handling, and recovery strategies.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import json
import time

from src.edge_case_handler import EdgeCaseHandler, EdgeCaseType
from src.interfaces import Document

class TestEdgeCaseHandler(unittest.TestCase):
    """Test suite for edge case handling functionality"""
    
    def setUp(self):
        """Set up before each test"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        
        # Initialize edge case handler
        self.handler = EdgeCaseHandler(log_dir=self.log_dir)
        
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
    
    def test_handle_edge_case(self):
        """Test basic edge case handling"""
        # Handle an edge case
        result = self.handler.handle_edge_case(
            EdgeCaseType.LLM_EXTRACTION_FAILURE,
            self.test_doc.filename,
            {"error": "Test error"},
            "retry"
        )
        
        # Check result
        self.assertTrue(result["handled"])
        self.assertEqual(result["case_type"], EdgeCaseType.LLM_EXTRACTION_FAILURE.value)
        self.assertEqual(result["recovery_status"], "retry_attempted")
        
        # Check stats
        stats = self.handler.get_edge_case_stats()
        self.assertEqual(stats["total_cases"], 1)
        self.assertEqual(stats["by_type"][EdgeCaseType.LLM_EXTRACTION_FAILURE.value], 1)
    
    def test_recovery_strategies(self):
        """Test different recovery strategies"""
        strategies = ["retry", "fallback", "skip", "manual_review"]
        
        for strategy in strategies:
            result = self.handler.handle_edge_case(
                EdgeCaseType.UNMATCHED_DOCUMENT,
                self.test_doc.filename,
                {"details": "Test details"},
                strategy
            )
            
            self.assertTrue(result["handled"])
            self.assertEqual(result["case_type"], EdgeCaseType.UNMATCHED_DOCUMENT.value)
            self.assertEqual(result["recovery_status"], f"{strategy}_used" if strategy != "manual_review" else "manual_review_required")
    
    def test_logging(self):
        """Test edge case logging"""
        # Handle multiple edge cases
        for case_type in EdgeCaseType:
            self.handler.handle_edge_case(
                case_type,
                self.test_doc.filename,
                {"test": "data"},
                "retry"
            )
        
        # Check log files
        log_files = list(self.log_dir.glob("*.json"))
        self.assertEqual(len(log_files), len(EdgeCaseType))
        
        # Check log content
        for log_file in log_files:
            with open(log_file) as f:
                log_entry = json.load(f)
                self.assertIn("timestamp", log_entry)
                self.assertIn("case_type", log_entry)
                self.assertIn("document_id", log_entry)
                self.assertIn("details", log_entry)
                self.assertIn("recovery_strategy", log_entry)
    
    def test_recent_edge_cases(self):
        """Test retrieving recent edge cases"""
        # Handle multiple edge cases
        for i in range(5):
            self.handler.handle_edge_case(
                EdgeCaseType.AMBIGUOUS_COMPLIANCE,
                f"doc_{i}.pdf",
                {"test": "data"},
                "retry"
            )
            time.sleep(0.1)  # Ensure different timestamps
        
        # Get recent cases
        recent_cases = self.handler.get_recent_edge_cases(limit=3)
        self.assertEqual(len(recent_cases), 3)
        
        # Check order (most recent first)
        self.assertEqual(recent_cases[0]["document_id"], "doc_4.pdf")
        self.assertEqual(recent_cases[1]["document_id"], "doc_3.pdf")
        self.assertEqual(recent_cases[2]["document_id"], "doc_2.pdf")
    
    def test_unknown_recovery_strategy(self):
        """Test handling unknown recovery strategy"""
        result = self.handler.handle_edge_case(
            EdgeCaseType.CORRUPTED_EVALUATION,
            self.test_doc.filename,
            {"error": "Test error"},
            "unknown_strategy"
        )
        
        self.assertTrue(result["handled"])
        self.assertEqual(result["recovery_status"], "unknown_strategy")

if __name__ == "__main__":
    unittest.main() 