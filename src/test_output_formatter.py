"""
Test suite for the unified output formatter.
Tests all supported output formats for both individual documents and matrices.
"""

import unittest
import tempfile
import json
import os
import sys
import logging
import shutil
import csv
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any, Optional, Union

# Add the src directory to the path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the modules under test
from output_format import (
    ValidationStatus,
    ValidationMetadata,
    ValidationItem,
    ValidationCategory,
    ValidationResult,
    ValidationResultFormatter
)

from compliance_evaluator import (
    ComplianceLevel,
    ComplianceResult
)

from output_formatter import (
    OutputFormatter,
    OutputFormat,
    OutputType
)

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class TestOutputFormatter(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create a test output directory
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.test_dir / "outputs"
        self.output_dir.mkdir(exist_ok=True)
        
        # Create a logger for tests
        self.logger = logging.getLogger("test_output_formatter")
        
        # Initialize the formatter
        self.formatter = OutputFormatter(
            include_details=True,
            include_justifications=True,
            include_confidence=True,
            include_metadata=True,
            visualization_style="color",
            logger=self.logger
        )
        
        # Create sample validation result
        self.sample_metadata = ValidationMetadata(
            timestamp=datetime.now().timestamp(),
            validator_version="1.0.0",
            mode="static",
            confidence_score=0.95,
            processing_time_ms=100.0,
            warnings=["Sample warning"]
        )
        
        # Create sample validation items
        self.passed_item = ValidationItem(
            id="item1",
            name="Password Policy",
            status=ValidationStatus.PASSED,
            confidence_score=0.9,
            details={
                "justification": "Password policy was found and meets requirements",
                "matched_keywords": ["password", "policy", "requirements"]
            },
            errors=[],
            warnings=[]
        )
        
        self.failed_item = ValidationItem(
            id="item2",
            name="Two-Factor Authentication",
            status=ValidationStatus.FAILED,
            confidence_score=0.85,
            details={
                "justification": "Two-factor authentication not implemented",
                "matched_keywords": [],
                "missing_keywords": ["2fa", "two-factor", "mfa"]
            },
            errors=["Required security feature missing"],
            warnings=[]
        )
        
        self.partial_item = ValidationItem(
            id="item3",
            name="Data Encryption",
            status=ValidationStatus.PARTIAL,
            confidence_score=0.75,
            details={
                "justification": "Data encryption in transit but not at rest",
                "matched_keywords": ["encryption", "tls", "ssl"],
                "missing_keywords": ["at rest", "storage"]
            },
            errors=[],
            warnings=["Incomplete implementation"]
        )
        
        # Create sample categories
        self.access_category = ValidationCategory(
            id="cat1",
            name="Access Control",
            status=ValidationStatus.PARTIAL,
            confidence_score=0.88,
            items=[self.passed_item, self.failed_item],
            errors=[],
            warnings=["Mixed compliance in this category"]
        )
        
        self.data_category = ValidationCategory(
            id="cat2",
            name="Data Protection",
            status=ValidationStatus.PARTIAL,
            confidence_score=0.75,
            items=[self.partial_item],
            errors=[],
            warnings=["Needs improvement"]
        )
        
        # Create sample validation result
        self.sample_result = ValidationResult(
            document_id="doc1",
            document_name="security_policy.pdf",
            document_type="policy",
            status=ValidationStatus.PARTIAL,
            metadata=self.sample_metadata,
            categories=[self.access_category, self.data_category],
            errors=[],
            warnings=["Document requires updates to meet compliance"]
        )
        
        # Create sample compliance result
        self.sample_compliance_result = ComplianceResult(
            is_compliant=True,
            confidence=0.92,
            details={
                "document_info": {
                    "id": "doc2",
                    "name": "security_controls.pdf",
                    "type": "controls"
                },
                "mode_used": "dynamic",
                "timestamp": datetime.now().timestamp(),
                "processing_time": 0.5,
                "overall_compliance": ComplianceLevel.PARTIALLY_COMPLIANT.value,
                "requirement_results": {
                    "REQ001": {
                        "requirement": {
                            "id": "REQ001",
                            "description": "Password Policy",
                            "category": "Access Control",
                            "type": "mandatory",
                            "priority": "high"
                        },
                        "compliance_level": ComplianceLevel.FULLY_COMPLIANT.value,
                        "confidence_score": 0.95,
                        "justification": "Password policy meets all requirements",
                        "matched_keywords": ["password", "policy", "requirements"]
                    },
                    "REQ002": {
                        "requirement": {
                            "id": "REQ002",
                            "description": "Two-Factor Authentication",
                            "category": "Access Control",
                            "type": "mandatory",
                            "priority": "high"
                        },
                        "compliance_level": ComplianceLevel.NON_COMPLIANT.value,
                        "confidence_score": 0.90,
                        "justification": "Two-factor authentication not implemented",
                        "matched_keywords": []
                    },
                    "REQ003": {
                        "requirement": {
                            "id": "REQ003",
                            "description": "Data Encryption",
                            "category": "Data Protection",
                            "type": "mandatory",
                            "priority": "critical"
                        },
                        "compliance_level": ComplianceLevel.PARTIALLY_COMPLIANT.value,
                        "confidence_score": 0.85,
                        "justification": "Encryption in transit but not at rest",
                        "matched_keywords": ["encryption", "tls"]
                    }
                }
            }
        )
        
        # Create sample matrix data
        self.sample_compliance_matrix = {
            "doc1": self.sample_result,
            "doc2": self.sample_compliance_result
        }
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove test directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_formatter_initialization(self):
        """Test the formatter initialization"""
        formatter = OutputFormatter()
        self.assertIsNotNone(formatter)
        self.assertTrue(formatter.include_details)
        self.assertTrue(formatter.include_justifications)
        self.assertTrue(formatter.include_confidence)
        self.assertTrue(formatter.include_metadata)
        
        # Test with different options
        formatter2 = OutputFormatter(
            include_details=False,
            include_justifications=False,
            include_confidence=False,
            include_metadata=False,
            visualization_style="text"
        )
        self.assertFalse(formatter2.include_details)
        self.assertFalse(formatter2.include_justifications)
        self.assertFalse(formatter2.include_confidence)
        self.assertFalse(formatter2.include_metadata)
    
    def test_document_json_format(self):
        """Test JSON formatting of a document result"""
        # Format the result as JSON
        result = self.formatter.format_document_result(
            result=self.sample_result,
            output_format=OutputFormat.JSON
        )
        
        # Verify key elements are present
        self.assertEqual(result["document_id"], "doc1")
        self.assertEqual(result["document_name"], "security_policy.pdf")
        self.assertEqual(result["document_type"], "policy")
        self.assertEqual(result["status"], "partial")
        
        # Verify categories and items
        self.assertEqual(len(result["categories"]), 2)
        self.assertEqual(result["categories"][0]["name"], "Access Control")
        self.assertEqual(result["categories"][0]["items"][0]["name"], "Password Policy")
        
        # Test saving to file
        output_path = self.output_dir / "document_result.json"
        saved_result = self.formatter.format_document_result(
            result=self.sample_result,
            output_format=OutputFormat.JSON,
            output_path=output_path
        )
        
        # Verify file exists and contains correct data
        self.assertTrue(output_path.exists())
        with open(output_path) as f:
            loaded_data = json.load(f)
            self.assertEqual(loaded_data["document_id"], "doc1")
    
    def test_document_csv_format(self):
        """Test CSV formatting of a document result"""
        # Format the result as CSV
        csv_content = self.formatter.format_document_result(
            result=self.sample_result,
            output_format=OutputFormat.CSV
        )
        
        # Verify it's a string and contains key data
        self.assertIsInstance(csv_content, str)
        self.assertIn("security_policy.pdf", csv_content)
        self.assertIn("Access Control", csv_content)
        
        # Parse CSV content to verify structure
        lines = csv_content.strip().split('\n')
        reader = csv.reader(lines)
        rows = list(reader)
        
        # Verify key rows
        self.assertEqual(rows[0][0], "Document ID")
        self.assertEqual(rows[0][1], "doc1")
        
        # Test saving to file
        output_path = self.output_dir / "document_result.csv"
        self.formatter.format_document_result(
            result=self.sample_result,
            output_format=OutputFormat.CSV,
            output_path=output_path
        )
        
        # Verify file exists
        self.assertTrue(output_path.exists())
    
    def test_document_html_format(self):
        """Test HTML formatting of a document result"""
        # Format the result as HTML
        html_content = self.formatter.format_document_result(
            result=self.sample_result,
            output_format=OutputFormat.HTML
        )
        
        # Verify it's a string and contains key elements
        self.assertIsInstance(html_content, str)
        self.assertIn("<!DOCTYPE html>", html_content)
        self.assertIn("security_policy.pdf", html_content)
        self.assertIn("Access Control", html_content)
        self.assertIn("Password Policy", html_content)
        
        # Verify HTML structure
        self.assertIn("<html>", html_content)
        self.assertIn("<head>", html_content)
        self.assertIn("<body>", html_content)
        self.assertIn("<style>", html_content)
        
        # Verify interactive elements
        self.assertIn("tooltip", html_content)
        
        # Test saving to file
        output_path = self.output_dir / "document_result.html"
        self.formatter.format_document_result(
            result=self.sample_result,
            output_format=OutputFormat.HTML,
            output_path=output_path
        )
        
        # Verify file exists
        self.assertTrue(output_path.exists())
    
    def test_document_markdown_format(self):
        """Test Markdown formatting of a document result"""
        # Format the result as Markdown
        md_content = self.formatter.format_document_result(
            result=self.sample_result,
            output_format=OutputFormat.MARKDOWN
        )
        
        # Verify it's a string and contains key elements
        self.assertIsInstance(md_content, str)
        self.assertIn("# Compliance Report:", md_content)
        self.assertIn("security_policy.pdf", md_content)
        self.assertIn("## Document Information", md_content)
        self.assertIn("## Validation Results", md_content)
        self.assertIn("Access Control", md_content)
        
        # Verify Markdown tables
        self.assertIn("| Item | Status |", md_content)
        
        # Test saving to file
        output_path = self.output_dir / "document_result.md"
        self.formatter.format_document_result(
            result=self.sample_result,
            output_format=OutputFormat.MARKDOWN,
            output_path=output_path
        )
        
        # Verify file exists
        self.assertTrue(output_path.exists())
    
    @unittest.skipIf("pandas" not in sys.modules or "openpyxl" not in sys.modules,
                   "pandas or openpyxl not installed")
    def test_document_excel_format(self):
        """Test Excel formatting of a document result"""
        # Format the result as Excel
        output_path = self.output_dir / "document_result.xlsx"
        excel_path = self.formatter.format_document_result(
            result=self.sample_result,
            output_format=OutputFormat.EXCEL,
            output_path=output_path
        )
        
        # Verify returned path matches provided path
        self.assertEqual(excel_path, output_path)
        
        # Verify file exists
        self.assertTrue(output_path.exists())
    
    def test_compliance_result_conversion(self):
        """Test conversion of ComplianceResult to standard format"""
        # Convert compliance result to standard format
        result = self.formatter._convert_compliance_result(self.sample_compliance_result)
        
        # Verify key elements are present
        self.assertEqual(result["document_id"], "doc2")
        self.assertEqual(result["document_name"], "security_controls.pdf")
        self.assertEqual(result["document_type"], "controls")
        
        # Verify categories were created from requirements
        categories = result["categories"]
        self.assertEqual(len(categories), 2)  # Access Control and Data Protection
        
        # Find the Access Control category
        access_category = next((c for c in categories if c["name"] == "Access Control"), None)
        self.assertIsNotNone(access_category)
        self.assertEqual(len(access_category["items"]), 2)  # Password Policy and 2FA
        
        # Find the Data Protection category
        data_category = next((c for c in categories if c["name"] == "Data Protection"), None)
        self.assertIsNotNone(data_category)
        self.assertEqual(len(data_category["items"]), 1)  # Data Encryption
    
    def test_validation_result_conversion(self):
        """Test conversion of ValidationResult to DocumentComplianceReport format"""
        # Convert validation result to compliance report format
        result = self.formatter._convert_validation_result(self.sample_result)
        
        # Verify key elements are present
        self.assertEqual(result["document_id"], "doc1")
        self.assertEqual(result["document_info"]["name"], "security_policy.pdf")
        self.assertEqual(result["document_info"]["type"], "policy")
        
        # Verify requirements were created from items
        self.assertEqual(len(result["requirements"]), 3)
        
        # Verify requirement_results were created
        self.assertEqual(len(result["requirement_results"]), 3)
        self.assertIn("item1", result["requirement_results"])
        
        # Verify compliance levels were mapped correctly
        self.assertEqual(
            result["requirement_results"]["item1"]["compliance_level"],
            ComplianceLevel.FULLY_COMPLIANT.value
        )
        self.assertEqual(
            result["requirement_results"]["item2"]["compliance_level"],
            ComplianceLevel.NON_COMPLIANT.value
        )
        self.assertEqual(
            result["requirement_results"]["item3"]["compliance_level"],
            ComplianceLevel.PARTIALLY_COMPLIANT.value
        )
    
    def test_compliance_matrix_json_format(self):
        """Test JSON formatting of a compliance matrix"""
        # Format the matrix as JSON
        result = self.formatter.format_compliance_matrix(
            reports=self.sample_compliance_matrix,
            output_format=OutputFormat.JSON
        )
        
        # Verify key elements are present
        self.assertIn("documents", result)
        self.assertIn("requirements", result)
        self.assertIn("compliance_matrix", result)
        self.assertIn("summary", result)
        
        # Verify documents were included
        self.assertEqual(len(result["documents"]), 2)
        
        # Test saving to file
        output_path = self.output_dir / "compliance_matrix.json"
        self.formatter.format_compliance_matrix(
            reports=self.sample_compliance_matrix,
            output_format=OutputFormat.JSON,
            output_path=output_path
        )
        
        # Verify file exists
        self.assertTrue(output_path.exists())
    
    def test_compliance_matrix_other_formats(self):
        """Test other formats for compliance matrix"""
        formats = [OutputFormat.CSV, OutputFormat.HTML, OutputFormat.MARKDOWN]
        
        for fmt in formats:
            result = self.formatter.format_compliance_matrix(
                reports=self.sample_compliance_matrix,
                output_format=fmt
            )
            
            # Verify result is a string
            self.assertIsInstance(result, str)
            
            # Verify key elements are present in all formats
            self.assertIn("security_policy.pdf", result)
            self.assertIn("security_controls.pdf", result)
            
            # Test saving to file
            extension = fmt.value
            output_path = self.output_dir / f"compliance_matrix.{extension}"
            self.formatter.format_compliance_matrix(
                reports=self.sample_compliance_matrix,
                output_format=fmt,
                output_path=output_path
            )
            
            # Verify file exists
            self.assertTrue(output_path.exists())
    
    def test_generate_report_document(self):
        """Test generate_report method with document type"""
        # Generate a document report
        result = self.formatter.generate_report(
            data=self.sample_result,
            output_type=OutputType.DOCUMENT,
            output_format=OutputFormat.JSON
        )
        
        # Verify key elements are present
        self.assertEqual(result["document_id"], "doc1")
        self.assertEqual(result["document_name"], "security_policy.pdf")
        
        # Test with all formats
        formats = [
            OutputFormat.JSON,
            OutputFormat.CSV,
            OutputFormat.HTML,
            OutputFormat.MARKDOWN
        ]
        
        for fmt in formats:
            output_path = self.output_dir / f"document_report.{fmt.value}"
            self.formatter.generate_report(
                data=self.sample_result,
                output_type=OutputType.DOCUMENT,
                output_format=fmt,
                output_path=output_path
            )
            
            # Verify file exists
            self.assertTrue(output_path.exists())
    
    def test_generate_report_matrix(self):
        """Test generate_report method with matrix type"""
        # Generate a matrix report
        result = self.formatter.generate_report(
            data=self.sample_compliance_matrix,
            output_type=OutputType.MATRIX,
            output_format=OutputFormat.JSON
        )
        
        # Verify key elements are present
        self.assertIn("documents", result)
        self.assertIn("requirements", result)
        self.assertIn("compliance_matrix", result)
        
        # Test with all formats
        formats = [
            OutputFormat.JSON,
            OutputFormat.CSV,
            OutputFormat.HTML,
            OutputFormat.MARKDOWN
        ]
        
        for fmt in formats:
            output_path = self.output_dir / f"matrix_report.{fmt.value}"
            self.formatter.generate_report(
                data=self.sample_compliance_matrix,
                output_type=OutputType.MATRIX,
                output_format=fmt,
                output_path=output_path
            )
            
            # Verify file exists
            self.assertTrue(output_path.exists())
    
    def test_generate_report_summary(self):
        """Test generate_report method with summary type"""
        # Generate a document summary
        result = self.formatter.generate_report(
            data=self.sample_result,
            output_type=OutputType.SUMMARY,
            output_format=OutputFormat.JSON
        )
        
        # Verify key elements are present
        self.assertEqual(result["document_id"], "doc1")
        self.assertEqual(result["document_name"], "security_policy.pdf")
        self.assertIn("status_counts", result)
        self.assertIn("category_summary", result)
        
        # Generate a matrix summary
        result = self.formatter.generate_report(
            data=self.sample_compliance_matrix,
            output_type=OutputType.SUMMARY,
            output_format=OutputFormat.JSON
        )
        
        # Test with all formats
        formats = [
            OutputFormat.JSON,
            OutputFormat.CSV,
            OutputFormat.HTML,
            OutputFormat.MARKDOWN
        ]
        
        for fmt in formats:
            output_path = self.output_dir / f"summary_report.{fmt.value}"
            self.formatter.generate_report(
                data=self.sample_result,
                output_type=OutputType.SUMMARY,
                output_format=fmt,
                output_path=output_path
            )
            
            # Verify file exists
            self.assertTrue(output_path.exists())
    
    def test_visual_element_inclusion(self):
        """Test that visual elements are included in HTML and Excel formats"""
        # Generate HTML report
        html_content = self.formatter.generate_report(
            data=self.sample_result,
            output_type=OutputType.DOCUMENT,
            output_format=OutputFormat.HTML
        )
        
        # Verify visual elements are present
        self.assertIn("status-badge", html_content)  # Styled status badges
        self.assertIn("tooltip", html_content)      # Tooltips for details
        
        # Verify color coding
        self.assertIn("background-color", html_content)
        
        # Generate HTML summary with chart
        html_summary = self.formatter.generate_report(
            data=self.sample_result,
            output_type=OutputType.SUMMARY,
            output_format=OutputFormat.HTML
        )
        
        # Verify chart element is present
        self.assertIn("chart-container", html_summary)

    def test_integration_with_different_modes(self):
        """Test integration with both static and dynamic evaluation modes"""
        # Create a static mode result
        static_result = ValidationResult(
            document_id="static_doc",
            document_name="static_report.pdf",
            document_type="report",
            status=ValidationStatus.PASSED,
            metadata=ValidationMetadata(mode="static"),
            categories=[]
        )
        
        # Create a dynamic mode result
        dynamic_result = ComplianceResult(
            is_compliant=True,
            confidence=0.9,
            details={
                "document_info": {
                    "id": "dynamic_doc",
                    "name": "dynamic_report.pdf",
                    "type": "report"
                },
                "mode_used": "dynamic",
                "overall_compliance": ComplianceLevel.FULLY_COMPLIANT.value,
                "requirement_results": {}
            }
        )
        
        # Test formatting both types
        static_formatted = self.formatter.format_document_result(
            result=static_result,
            output_format=OutputFormat.JSON
        )
        
        dynamic_formatted = self.formatter.format_document_result(
            result=dynamic_result,
            output_format=OutputFormat.JSON
        )
        
        # Verify mode is preserved
        self.assertEqual(static_formatted["metadata"]["mode"], "static")
        self.assertEqual(dynamic_formatted["metadata"]["mode"], "dynamic")
        
        # Test combined matrix
        combined_matrix = {
            "static_doc": static_result,
            "dynamic_doc": dynamic_result
        }
        
        matrix_result = self.formatter.format_compliance_matrix(
            reports=combined_matrix,
            output_format=OutputFormat.JSON
        )
        
        # Verify both documents are included
        doc_ids = [doc["id"] for doc in matrix_result["documents"]]
        self.assertIn("static_doc", doc_ids)
        self.assertIn("dynamic_doc", doc_ids)


# Additional test to verify execution evidence
class TestOutputFormatterExecutionEvidence(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create an output directory for evidence
        self.evidence_dir = Path("execution_evidence")
        self.evidence_dir.mkdir(exist_ok=True)
        
        # Create sample data similar to TestOutputFormatter's
        self.formatter = OutputFormatter()
        self.sample_result = self._create_sample_validation_result()
        self.sample_matrix = {
            "doc1": self.sample_result,
            "doc2": self._create_sample_compliance_result()
        }
    
    def tearDown(self):
        """Clean up after tests"""
        # In this case, we'll keep the evidence directory for inspection
        pass
    
    def _create_sample_validation_result(self):
        """Create a sample validation result for testing"""
        # Create items
        items = [
            ValidationItem(
                id=f"item{i}",
                name=f"Test Item {i}",
                status=ValidationStatus.PASSED if i % 3 == 0 else 
                      (ValidationStatus.PARTIAL if i % 3 == 1 else ValidationStatus.FAILED),
                confidence_score=0.7 + (i % 3) * 0.1,
                details={"justification": f"Justification for item {i}"}
            )
            for i in range(1, 6)
        ]
        
        # Create categories
        categories = [
            ValidationCategory(
                id="cat1",
                name="Category A",
                status=ValidationStatus.PARTIAL,
                confidence_score=0.85,
                items=items[:3]
            ),
            ValidationCategory(
                id="cat2",
                name="Category B",
                status=ValidationStatus.PARTIAL,
                confidence_score=0.75,
                items=items[3:]
            )
        ]
        
        # Create validation result
        return ValidationResult(
            document_id="doc1",
            document_name="Test Document.pdf",
            document_type="report",
            status=ValidationStatus.PARTIAL,
            metadata=ValidationMetadata(
                timestamp=datetime.now().timestamp(),
                mode="static"
            ),
            categories=categories
        )
    
    def _create_sample_compliance_result(self):
        """Create a sample compliance result for testing"""
        return ComplianceResult(
            is_compliant=True,
            confidence=0.8,
            details={
                "document_info": {
                    "id": "doc2",
                    "name": "Compliance Document.pdf",
                    "type": "policy"
                },
                "mode_used": "dynamic",
                "overall_compliance": ComplianceLevel.PARTIALLY_COMPLIANT.value,
                "requirement_results": {
                    f"REQ00{i}": {
                        "requirement": {
                            "id": f"REQ00{i}",
                            "description": f"Requirement {i}",
                            "category": "Category " + ("A" if i <= 3 else "B"),
                            "type": "mandatory",
                            "priority": "medium"
                        },
                        "compliance_level": (
                            ComplianceLevel.FULLY_COMPLIANT.value if i % 3 == 0 else
                            ComplianceLevel.PARTIALLY_COMPLIANT.value if i % 3 == 1 else
                            ComplianceLevel.NON_COMPLIANT.value
                        ),
                        "confidence_score": 0.7 + (i % 3) * 0.1,
                        "justification": f"Justification for requirement {i}"
                    }
                    for i in range(1, 6)
                }
            }
        )
    
    def test_generate_execution_evidence(self):
        """Generate execution evidence for all formats and types"""
        # Test document outputs in all formats
        print("\nGenerating document output evidence...")
        for fmt in OutputFormat:
            # Skip Excel if pandas/openpyxl not installed
            if fmt == OutputFormat.EXCEL and ("pandas" not in sys.modules or "openpyxl" not in sys.modules):
                continue
                
            output_path = self.evidence_dir / f"document_{fmt.value}"
            
            # Use appropriate extension
            if fmt == OutputFormat.EXCEL:
                output_path = output_path.with_suffix(".xlsx")
            else:
                output_path = output_path.with_suffix(f".{fmt.value}")
                
            result = self.formatter.generate_report(
                data=self.sample_result,
                output_type=OutputType.DOCUMENT,
                output_format=fmt,
                output_path=output_path
            )
            
            print(f"  - Generated {fmt.value} document report: {output_path}")
            self.assertTrue(output_path.exists())
        
        # Test matrix outputs in all formats
        print("\nGenerating matrix output evidence...")
        for fmt in OutputFormat:
            # Skip Excel if pandas/openpyxl not installed
            if fmt == OutputFormat.EXCEL and ("pandas" not in sys.modules or "openpyxl" not in sys.modules):
                continue
                
            output_path = self.evidence_dir / f"matrix_{fmt.value}"
            
            # Use appropriate extension
            if fmt == OutputFormat.EXCEL:
                output_path = output_path.with_suffix(".xlsx")
            else:
                output_path = output_path.with_suffix(f".{fmt.value}")
                
            result = self.formatter.generate_report(
                data=self.sample_matrix,
                output_type=OutputType.MATRIX,
                output_format=fmt,
                output_path=output_path
            )
            
            print(f"  - Generated {fmt.value} matrix report: {output_path}")
            self.assertTrue(output_path.exists())
        
        # Test summary outputs in all formats
        print("\nGenerating summary output evidence...")
        for fmt in OutputFormat:
            # Skip Excel if pandas/openpyxl not installed
            if fmt == OutputFormat.EXCEL and ("pandas" not in sys.modules or "openpyxl" not in sys.modules):
                continue
                
            output_path = self.evidence_dir / f"summary_{fmt.value}"
            
            # Use appropriate extension
            if fmt == OutputFormat.EXCEL:
                output_path = output_path.with_suffix(".xlsx")
            else:
                output_path = output_path.with_suffix(f".{fmt.value}")
                
            result = self.formatter.generate_report(
                data=self.sample_result,
                output_type=OutputType.SUMMARY,
                output_format=fmt,
                output_path=output_path
            )
            
            print(f"  - Generated {fmt.value} summary report: {output_path}")
            self.assertTrue(output_path.exists())
        
        print("\nAll output formats successfully generated!")
        print(f"Evidence files available in: {self.evidence_dir.absolute()}")


if __name__ == "__main__":
    unittest.main()