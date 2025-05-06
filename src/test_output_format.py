"""
Test suite for the unified output format module.
"""

import unittest
from pathlib import Path
import json
import tempfile
import time
from datetime import datetime

from output_format import (
    ValidationStatus,
    ValidationLevel,
    ValidationMetadata,
    ValidationItem,
    ValidationCategory,
    ValidationResult,
    ValidationResultFormatter
)

class TestOutputFormat(unittest.TestCase):
    def setUp(self):
        """Set up test data"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Create sample validation result
        self.sample_metadata = ValidationMetadata(
            timestamp=time.time(),
            validator_version="1.0.0",
            mode="static",
            confidence_score=0.95,
            processing_time_ms=100.0,
            warnings=["Sample warning"]
        )
        
        self.sample_item = ValidationItem(
            id="item1",
            name="Test Item",
            status=ValidationStatus.PASSED,
            confidence_score=0.9,
            details={"key": "value"},
            errors=["Item error"],
            warnings=["Item warning"]
        )
        
        self.sample_category = ValidationCategory(
            id="cat1",
            name="Test Category",
            status=ValidationStatus.PARTIAL,
            confidence_score=0.85,
            items=[self.sample_item],
            errors=["Category error"],
            warnings=["Category warning"]
        )
        
        self.sample_result = ValidationResult(
            document_id="doc1",
            document_name="test.pdf",
            document_type="invoice",
            status=ValidationStatus.PASSED,
            metadata=self.sample_metadata,
            categories=[self.sample_category],
            errors=["Document error"],
            warnings=["Document warning"]
        )
    
    def test_validation_status_enum(self):
        """Test ValidationStatus enum values"""
        self.assertEqual(ValidationStatus.PASSED.value, "passed")
        self.assertEqual(ValidationStatus.FAILED.value, "failed")
        self.assertEqual(ValidationStatus.PARTIAL.value, "partial")
        self.assertEqual(ValidationStatus.UNKNOWN.value, "unknown")
        self.assertEqual(ValidationStatus.ERROR.value, "error")
    
    def test_validation_level_enum(self):
        """Test ValidationLevel enum values"""
        self.assertEqual(ValidationLevel.DOCUMENT.value, "document")
        self.assertEqual(ValidationLevel.CATEGORY.value, "category")
        self.assertEqual(ValidationLevel.ITEM.value, "item")
    
    def test_validation_metadata(self):
        """Test ValidationMetadata creation and attributes"""
        metadata = ValidationMetadata()
        self.assertIsInstance(metadata.timestamp, float)
        self.assertEqual(metadata.validator_version, "1.0.0")
        self.assertEqual(metadata.mode, "static")
        self.assertEqual(metadata.confidence_score, 1.0)
        self.assertEqual(metadata.processing_time_ms, 0.0)
        self.assertEqual(metadata.warnings, [])
    
    def test_validation_item(self):
        """Test ValidationItem creation and attributes"""
        item = ValidationItem(
            id="test",
            name="Test",
            status=ValidationStatus.PASSED
        )
        self.assertEqual(item.id, "test")
        self.assertEqual(item.name, "Test")
        self.assertEqual(item.status, ValidationStatus.PASSED)
        self.assertEqual(item.confidence_score, 1.0)
        self.assertEqual(item.details, {})
        self.assertEqual(item.errors, [])
        self.assertEqual(item.warnings, [])
    
    def test_validation_category(self):
        """Test ValidationCategory creation and attributes"""
        category = ValidationCategory(
            id="test",
            name="Test",
            status=ValidationStatus.PASSED
        )
        self.assertEqual(category.id, "test")
        self.assertEqual(category.name, "Test")
        self.assertEqual(category.status, ValidationStatus.PASSED)
        self.assertEqual(category.confidence_score, 1.0)
        self.assertEqual(category.items, [])
        self.assertEqual(category.errors, [])
        self.assertEqual(category.warnings, [])
    
    def test_validation_result(self):
        """Test ValidationResult creation and attributes"""
        result = ValidationResult(
            document_id="test",
            document_name="test.pdf",
            document_type="invoice",
            status=ValidationStatus.PASSED,
            metadata=self.sample_metadata
        )
        self.assertEqual(result.document_id, "test")
        self.assertEqual(result.document_name, "test.pdf")
        self.assertEqual(result.document_type, "invoice")
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.metadata, self.sample_metadata)
        self.assertEqual(result.categories, [])
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
    
    def test_serialization_deserialization(self):
        """Test serialization and deserialization of ValidationResult"""
        # Convert to dict
        data = ValidationResultFormatter.to_dict(self.sample_result)
        
        # Verify structure
        self.assertEqual(data["document_id"], "doc1")
        self.assertEqual(data["document_name"], "test.pdf")
        self.assertEqual(data["document_type"], "invoice")
        self.assertEqual(data["status"], "passed")
        self.assertEqual(data["metadata"]["mode"], "static")
        self.assertEqual(data["categories"][0]["name"], "Test Category")
        self.assertEqual(data["categories"][0]["items"][0]["name"], "Test Item")
        
        # Convert back to ValidationResult
        result = ValidationResultFormatter.from_dict(data)
        
        # Verify round-trip
        self.assertEqual(result.document_id, self.sample_result.document_id)
        self.assertEqual(result.document_name, self.sample_result.document_name)
        self.assertEqual(result.document_type, self.sample_result.document_type)
        self.assertEqual(result.status, self.sample_result.status)
        self.assertEqual(result.metadata.mode, self.sample_result.metadata.mode)
        self.assertEqual(result.categories[0].name, self.sample_result.categories[0].name)
        self.assertEqual(result.categories[0].items[0].name, self.sample_result.categories[0].items[0].name)
    
    def test_schema_validation(self):
        """Test schema validation"""
        # Valid data
        data = ValidationResultFormatter.to_dict(self.sample_result)
        errors = ValidationResultFormatter.validate_schema(data)
        self.assertEqual(errors, [])
        
        # Invalid data (missing required field)
        invalid_data = data.copy()
        del invalid_data["document_id"]
        errors = ValidationResultFormatter.validate_schema(invalid_data)
        self.assertGreater(len(errors), 0)
    
    def test_file_io(self):
        """Test saving and loading validation results"""
        output_path = self.test_dir / "test_result.json"
        
        # Save result
        ValidationResultFormatter.save_to_file(self.sample_result, output_path)
        
        # Verify file exists and is valid JSON
        self.assertTrue(output_path.exists())
        with open(output_path) as f:
            data = json.load(f)
            self.assertEqual(data["document_id"], "doc1")
        
        # Load result
        loaded_result = ValidationResultFormatter.load_from_file(output_path)
        
        # Verify loaded result
        self.assertEqual(loaded_result.document_id, self.sample_result.document_id)
        self.assertEqual(loaded_result.document_name, self.sample_result.document_name)
        self.assertEqual(loaded_result.document_type, self.sample_result.document_type)
    
    def test_filter_results(self):
        """Test filtering validation results"""
        # Create result with mixed statuses
        passed_item = ValidationItem(
            id="passed",
            name="Passed Item",
            status=ValidationStatus.PASSED,
            confidence_score=0.9
        )
        failed_item = ValidationItem(
            id="failed",
            name="Failed Item",
            status=ValidationStatus.FAILED,
            confidence_score=0.8
        )
        
        category = ValidationCategory(
            id="test",
            name="Test Category",
            status=ValidationStatus.PARTIAL,
            items=[passed_item, failed_item]
        )
        
        result = ValidationResult(
            document_id="test",
            document_name="test.pdf",
            document_type="invoice",
            status=ValidationStatus.PARTIAL,
            metadata=self.sample_metadata,
            categories=[category]
        )
        
        # Filter for passed items only
        filtered = ValidationResultFormatter.filter_results(
            result,
            status=ValidationStatus.PASSED
        )
        self.assertEqual(len(filtered.categories[0].items), 1)
        self.assertEqual(filtered.categories[0].items[0].id, "passed")
        
        # Filter for high confidence
        filtered = ValidationResultFormatter.filter_results(
            result,
            min_confidence=0.85
        )
        self.assertEqual(len(filtered.categories[0].items), 1)
        self.assertEqual(filtered.categories[0].items[0].id, "passed")
    
    def test_pretty_print(self):
        """Test pretty printing of validation results"""
        output = ValidationResultFormatter.pretty_print(self.sample_result)
        
        # Verify key information is present
        self.assertIn("test.pdf", output)
        self.assertIn("invoice", output)
        self.assertIn("passed", output)
        self.assertIn("Test Category", output)
        self.assertIn("Test Item", output)
        self.assertIn("Document warning", output)
        self.assertIn("Category warning", output)
        self.assertIn("Item warning", output)
        
        # Verify formatting
        self.assertIn("Document:", output)
        self.assertIn("Status:", output)
        self.assertIn("Confidence:", output)
        self.assertIn("Mode:", output)
        self.assertIn("Timestamp:", output)
        self.assertIn("⚠", output)  # Warning symbol
        self.assertIn("✗", output)  # Error symbol

if __name__ == "__main__":
    unittest.main() 