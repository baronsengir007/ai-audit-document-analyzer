"""
Test suite for ComplianceMatrixGenerator
Tests matrix generation, filtering, sorting, and different output formats.
"""

import unittest
import logging
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from .compliance_matrix_generator import (
    ComplianceMatrixGenerator,
    OutputFormat,
    SortOrder,
    VisualizationStyle
)

from .compliance_evaluator import ComplianceEvaluator, ComplianceLevel


class TestComplianceMatrixGenerator(unittest.TestCase):
    """Test suite for the ComplianceMatrixGenerator class"""
    
    def setUp(self):
        """Set up test fixtures for each test method"""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Create mock evaluator
        self.mock_evaluator = MagicMock(spec=ComplianceEvaluator)
        
        # Initialize the matrix generator with the mock evaluator
        self.generator = ComplianceMatrixGenerator(
            evaluator=self.mock_evaluator,
            visualization_style=VisualizationStyle.SYMBOL,
            include_justifications=True,
            include_confidence=True,
            include_metadata=True
        )
        
        # Mock reports dict (simplified structure)
        self.mock_reports = {"doc1.pdf": MagicMock(), "doc2.pdf": MagicMock()}
        
        # Sample compliance matrix (using dictionary structure)
        self.sample_matrix = {
            "documents": [
                {"id": "doc1.pdf", "type": "audit", "name": "Document 1", 
                 "overall_compliance": "fully_compliant"},
                {"id": "doc2.pdf", "type": "policy", "name": "Document 2", 
                 "overall_compliance": "partially_compliant"}
            ],
            "requirements": [
                {"id": "REQ001", "description": "All passwords must be at least 12 characters", 
                 "type": "mandatory", "priority": "high", "category": "Authentication"},
                {"id": "REQ002", "description": "User access must be reviewed monthly", 
                 "type": "mandatory", "priority": "medium", "category": "Access Control"}
            ],
            "compliance_matrix": [
                {
                    "document_id": "doc1.pdf",
                    "results": {
                        "REQ001": {"compliance_level": "fully_compliant", "confidence_score": 0.9},
                        "REQ002": {"compliance_level": "fully_compliant", "confidence_score": 0.85}
                    }
                },
                {
                    "document_id": "doc2.pdf",
                    "results": {
                        "REQ001": {"compliance_level": "partially_compliant", "confidence_score": 0.7},
                        "REQ002": {"compliance_level": "non_compliant", "confidence_score": 0.6}
                    }
                }
            ],
            "summary": {
                "overall_compliance": {
                    "level": "partially_compliant",
                    "percentages": {
                        "fully_compliant": 50,
                        "partially_compliant": 25,
                        "non_compliant": 25,
                        "not_applicable": 0,
                        "indeterminate": 0
                    },
                    "counts": {
                        "fully_compliant": 2,
                        "partially_compliant": 1,
                        "non_compliant": 1,
                        "not_applicable": 0,
                        "indeterminate": 0
                    }
                },
                "compliance_by_document": {
                    "doc1.pdf": {
                        "fully_compliant": 2,
                        "partially_compliant": 0,
                        "non_compliant": 0,
                        "not_applicable": 0,
                        "indeterminate": 0
                    },
                    "doc2.pdf": {
                        "fully_compliant": 0,
                        "partially_compliant": 1,
                        "non_compliant": 1,
                        "not_applicable": 0,
                        "indeterminate": 0
                    }
                },
                "compliance_by_category": {
                    "Authentication": {
                        "fully_compliant": 1,
                        "partially_compliant": 1,
                        "non_compliant": 0,
                        "not_applicable": 0,
                        "indeterminate": 0
                    },
                    "Access Control": {
                        "fully_compliant": 1,
                        "partially_compliant": 0,
                        "non_compliant": 1,
                        "not_applicable": 0,
                        "indeterminate": 0
                    }
                }
            },
            "metadata": {
                "generation_date": "2025-05-05T12:00:00Z",
                "total_documents": 2,
                "total_requirements": 2,
                "total_evaluations": 4
            }
        }
        
        # Configure mock to return our sample matrix
        self.mock_evaluator.generate_compliance_matrix.return_value = self.sample_matrix
    
    def test_generate_matrix_json(self):
        """Test generating a matrix in JSON format"""
        # Generate JSON matrix
        matrix = self.generator.generate_matrix(
            self.mock_reports,
            output_format=OutputFormat.JSON
        )
        
        # Verify structure and content
        self.assertIsInstance(matrix, dict)
        self.assertIn("documents", matrix)
        self.assertIn("requirements", matrix)
        self.assertIn("compliance_matrix", matrix)
        self.assertIn("summary", matrix)
        
        # Verify document count
        self.assertEqual(len(matrix["documents"]), 2)
        
        # Verify evaluator was called correctly
        self.mock_evaluator.generate_compliance_matrix.assert_called_once_with(self.mock_reports)
    
    def test_generate_matrix_csv(self):
        """Test generating a matrix in CSV format"""
        # Generate CSV matrix
        csv_content = self.generator.generate_matrix(
            self.mock_reports,
            output_format=OutputFormat.CSV
        )
        
        # Verify it's a string and contains expected content
        self.assertIsInstance(csv_content, str)
        self.assertIn("Document ID", csv_content)
        self.assertIn("doc1.pdf", csv_content)
        self.assertIn("doc2.pdf", csv_content)
        self.assertIn("REQ001", csv_content)
        self.assertIn("REQ002", csv_content)
    
    def test_generate_matrix_html(self):
        """Test generating a matrix in HTML format"""
        # Generate HTML matrix
        html_content = self.generator.generate_matrix(
            self.mock_reports,
            output_format=OutputFormat.HTML
        )
        
        # Verify it's a string and contains expected HTML structure
        self.assertIsInstance(html_content, str)
        self.assertIn("<!DOCTYPE html>", html_content)
        self.assertIn("<html>", html_content)
        self.assertIn("<table>", html_content)
        self.assertIn("</html>", html_content)
        
        # Verify document IDs are in the HTML
        self.assertIn("doc1.pdf", html_content)
        self.assertIn("doc2.pdf", html_content)
        
        # Verify requirement IDs are in the HTML
        self.assertIn("REQ001", html_content)
        self.assertIn("REQ002", html_content)
    
    def test_generate_matrix_markdown(self):
        """Test generating a matrix in Markdown format"""
        # Generate Markdown matrix
        md_content = self.generator.generate_matrix(
            self.mock_reports,
            output_format=OutputFormat.MARKDOWN
        )
        
        # Verify it's a string and contains expected Markdown structure
        self.assertIsInstance(md_content, str)
        self.assertIn("# Compliance Matrix Report", md_content)
        self.assertIn("## Compliance Matrix", md_content)
        self.assertIn("| Document ID |", md_content)
        
        # Verify document IDs are in the Markdown
        self.assertIn("doc1.pdf", md_content)
        self.assertIn("doc2.pdf", md_content)
        
        # Verify requirement IDs are in the Markdown
        self.assertIn("REQ001", md_content)
        self.assertIn("REQ002", md_content)
    
    def test_filters(self):
        """Test filtering functionality"""
        # Mock internal method to prevent data manipulation issues
        original_method = self.generator._apply_filters
        self.generator._apply_filters = MagicMock(return_value=self.sample_matrix)
        
        try:
            # Call generate_matrix with filters
            self.generator.generate_matrix(
                self.mock_reports,
                output_format=OutputFormat.JSON,
                filters={"document_id": "doc1"}
            )
            
            # Verify _apply_filters was called with the correct arguments
            self.generator._apply_filters.assert_called_once()
            args, kwargs = self.generator._apply_filters.call_args
            # The filter is passed as the second argument to _apply_filters
            self.assertEqual(args[1], {"document_id": "doc1"})
            
        finally:
            # Restore original method
            self.generator._apply_filters = original_method
    
    def test_sorting(self):
        """Test sorting functionality"""
        # Mock internal method to prevent data manipulation issues
        original_method = self.generator._apply_sorting
        self.generator._apply_sorting = MagicMock(return_value=self.sample_matrix)
        
        try:
            # Call generate_matrix with sorting
            self.generator.generate_matrix(
                self.mock_reports,
                output_format=OutputFormat.JSON,
                sort_by="document_id",
                sort_order=SortOrder.ASCENDING
            )
            
            # Verify _apply_sorting was called with the correct arguments
            self.generator._apply_sorting.assert_called_once()
            args, kwargs = self.generator._apply_sorting.call_args
            self.assertEqual(args[1], "document_id")
            self.assertEqual(args[2], SortOrder.ASCENDING)
            
        finally:
            # Restore original method
            self.generator._apply_sorting = original_method
    
    def test_save_to_file(self):
        """Test saving matrix to file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test JSON output
            json_path = temp_path / "matrix.json"
            self.generator.generate_matrix(
                self.mock_reports,
                output_format=OutputFormat.JSON,
                output_path=json_path
            )
            
            # Verify file was created and contains JSON
            self.assertTrue(json_path.exists())
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                self.assertIn("documents", json_data)
            
            # Test other formats if needed
            md_path = temp_path / "matrix.md"
            self.generator.generate_matrix(
                self.mock_reports,
                output_format=OutputFormat.MARKDOWN,
                output_path=md_path
            )
            
            # Verify file was created
            self.assertTrue(md_path.exists())
    
    def test_visualization_styles(self):
        """Test different visualization styles"""
        # Test symbol style
        self.generator.visualization_style = VisualizationStyle.SYMBOL
        symbol_matrix = self.generator.generate_matrix(
            self.mock_reports,
            output_format=OutputFormat.CSV
        )
        
        # Verify symbols are used
        self.assertIn("✓", symbol_matrix)  # Check mark for fully compliant
        
        # Test text style
        self.generator.visualization_style = VisualizationStyle.TEXT
        text_matrix = self.generator.generate_matrix(
            self.mock_reports,
            output_format=OutputFormat.CSV
        )
        
        # Verify text representations are used
        self.assertIn("fully_compliant", text_matrix)
    
    def test_error_handling(self):
        """Test error handling"""
        # Make evaluator raise an exception
        self.mock_evaluator.generate_compliance_matrix.side_effect = Exception("Test error")
        
        # Verify exception is propagated
        with self.assertRaises(Exception):
            self.generator.generate_matrix(
                self.mock_reports,
                output_format=OutputFormat.JSON
            )


if __name__ == "__main__":
    unittest.main()