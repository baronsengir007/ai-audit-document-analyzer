"""
Test suite for core interfaces and data types.
"""

import unittest
from pathlib import Path
import tempfile
import shutil
import json
import time
from datetime import datetime

from src.interfaces import (
    Document,
    ComplianceResult,
    ValidationResult,
    DocumentProcessor,
    ValidationStrategy,
    ValidationMode,
    ValidationResultSerializer,
    StaticDocumentProcessor,
    StaticValidationStrategy,
    StaticValidationMode
)

class TestInterfaces(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_doc = Document(
            filename="test.pdf",
            content="This is a test document with invoice and total amount",
            classification="invoice",
            metadata={"file_type": "pdf"},
            source_path=Path("test.pdf")
        )

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_document_creation(self):
        """Test Document dataclass creation and attributes"""
        doc = Document(
            filename="test.pdf",
            content="test content",
            classification="invoice",
            metadata={"key": "value"},
            source_path=Path("test.pdf")
        )
        
        self.assertEqual(doc.filename, "test.pdf")
        self.assertEqual(doc.content, "test content")
        self.assertEqual(doc.classification, "invoice")
        self.assertEqual(doc.metadata, {"key": "value"})
        self.assertEqual(doc.source_path, Path("test.pdf"))

    def test_validation_result_creation(self):
        """Test ValidationResult dataclass creation and attributes"""
        result = ValidationResult(
            document=self.test_doc,
            status="complete",
            validation_results={"key": "value"},
            mode="static",
            timestamp=time.time()
        )
        
        self.assertEqual(result.document, self.test_doc)
        self.assertEqual(result.status, "complete")
        self.assertEqual(result.validation_results, {"key": "value"})
        self.assertEqual(result.mode, "static")
        self.assertIsNone(result.error)

    def test_validation_result_serialization(self):
        """Test serialization and deserialization of ValidationResult"""
        original = ValidationResult(
            document=self.test_doc,
            status="complete",
            validation_results={"key": "value"},
            mode="static",
            timestamp=time.time()
        )
        
        # Serialize
        serialized = ValidationResultSerializer.to_json(original)
        
        # Verify serialized structure
        self.assertEqual(serialized["document"]["filename"], "test.pdf")
        self.assertEqual(serialized["status"], "complete")
        self.assertEqual(serialized["validation_results"], {"key": "value"})
        self.assertEqual(serialized["mode"], "static")
        
        # Deserialize
        deserialized = ValidationResultSerializer.from_json(serialized)
        
        # Verify deserialized object
        self.assertEqual(deserialized.document.filename, "test.pdf")
        self.assertEqual(deserialized.status, "complete")
        self.assertEqual(deserialized.validation_results, {"key": "value"})
        self.assertEqual(deserialized.mode, "static")

    def test_static_document_processor(self):
        """Test StaticDocumentProcessor implementation"""
        processor = StaticDocumentProcessor()
        
        # Create a test PDF file
        test_pdf = Path(self.test_dir) / "test.pdf"
        with open(test_pdf, "w") as f:
            f.write("This is a test PDF")
        
        # Process document
        doc = processor.process_document(test_pdf)
        
        # Verify document attributes
        self.assertEqual(doc.filename, "test.pdf")
        self.assertEqual(doc.classification, "unknown")  # Default classification
        self.assertEqual(doc.metadata["file_type"], "pdf")
        self.assertEqual(doc.source_path, test_pdf)

    def test_static_validation_strategy(self):
        """Test StaticValidationStrategy implementation"""
        strategy = StaticValidationStrategy(
            checklist_map={"invoice": ["invoice", "total"]},
            type_to_checklist_id={"invoice": "invoice"}
        )
        
        # Test validation
        result = strategy.validate(self.test_doc)
        
        # Verify result
        self.assertEqual(result.status, "complete")
        self.assertEqual(result.mode, "static")
        self.assertIn("present_keywords", result.validation_results)
        self.assertIn("missing_keywords", result.validation_results)

    def test_static_validation_mode(self):
        """Test StaticValidationMode implementation"""
        mode = StaticValidationMode()
        mode.initialize({
            "checklist_map": {"invoice": ["invoice", "total"]},
            "type_to_checklist_id": {"invoice": "invoice"},
            "max_workers": 2
        })
        
        # Test batch processing
        results = mode.process_batch([self.test_doc])
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, "complete")
        
        # Test saving results
        output_path = Path(self.test_dir) / "results.json"
        mode.save_results(results, output_path)
        
        # Verify saved results
        self.assertTrue(output_path.exists())
        with open(output_path) as f:
            saved_results = json.load(f)
            self.assertEqual(len(saved_results), 1)
            self.assertEqual(saved_results[0]["status"], "complete")

    def test_error_handling(self):
        """Test error handling in validation strategy"""
        strategy = StaticValidationStrategy(
            checklist_map={},
            type_to_checklist_id={}
        )
        
        # Test with invalid document
        result = strategy.validate(Document(
            filename="invalid.pdf",
            content="",
            classification="unknown",
            metadata={}
        ))
        
        # Verify error handling
        self.assertEqual(result.status, "unknown_type")
        self.assertEqual(result.mode, "static")

    def test_performance(self):
        """Test performance of batch processing"""
        mode = StaticValidationMode()
        mode.initialize({
            "checklist_map": {"invoice": ["invoice", "total"]},
            "type_to_checklist_id": {"invoice": "invoice"},
            "max_workers": 4
        })
        
        # Create multiple test documents
        documents = [
            Document(
                filename=f"test_{i}.pdf",
                content="This is a test document with invoice and total amount",
                classification="invoice",
                metadata={"file_type": "pdf"}
            )
            for i in range(10)
        ]
        
        # Time batch processing
        start_time = time.time()
        results = mode.process_batch(documents)
        end_time = time.time()
        
        # Verify all documents were processed
        self.assertEqual(len(results), 10)
        # Verify processing time is reasonable (adjust threshold as needed)
        self.assertLess(end_time - start_time, 2.0)

if __name__ == "__main__":
    unittest.main() 