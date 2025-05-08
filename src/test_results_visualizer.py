"""
Tests for the results visualizer module.
"""

import unittest
import json
import os
import re
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
from datetime import datetime

from results_visualizer import ResultsVisualizer, generate_visualization_reports

class TestResultsVisualizer(unittest.TestCase):
    """Test cases for the ResultsVisualizer class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        
        # Sample verification result for testing
        self.verification_result = {
            "found_types": [
                {
                    "id": "privacy_policy",
                    "name": "Privacy Policy",
                    "required": True,
                    "description": "Document explaining how user data is collected",
                    "document_count": 2
                },
                {
                    "id": "security_policy",
                    "name": "Security Policy",
                    "required": True,
                    "description": "Document outlining security measures",
                    "document_count": 1
                }
            ],
            "missing_types": [
                {
                    "id": "incident_response",
                    "name": "Incident Response Plan",
                    "required": True,
                    "description": "Document detailing response procedures"
                }
            ],
            "extra_types": [
                {
                    "id": "test_report",
                    "name": "Test Report",
                    "required": False,
                    "description": "Document containing test results",
                    "document_count": 1
                },
                {
                    "id": "unknown",
                    "name": "Unknown",
                    "required": False,
                    "description": "Documents that couldn't be classified",
                    "document_count": 2
                }
            ],
            "documents_by_type": {
                "privacy_policy": [
                    {
                        "filename": "privacy_policy1.pdf",
                        "confidence": 0.92
                    },
                    {
                        "filename": "privacy_policy2.pdf",
                        "confidence": 0.88
                    }
                ],
                "security_policy": [
                    {
                        "filename": "security_controls.pdf",
                        "confidence": 0.85
                    }
                ],
                "test_report": [
                    {
                        "filename": "test_results.pdf",
                        "confidence": 0.90
                    }
                ],
                "unknown": [
                    {
                        "filename": "unknown1.pdf",
                        "confidence": 0.45
                    },
                    {
                        "filename": "unknown2.pdf",
                        "confidence": 0.30
                    }
                ]
            },
            "unclassified_documents": [
                {
                    "filename": "low_confidence.pdf",
                    "type_id": "privacy_policy",
                    "confidence": 0.65
                }
            ],
            "coverage": 0.6667,
            "total_documents": 6,
            "total_required_types": 3,
            "total_found_required_types": 2,
            "total_missing_types": 1,
            "total_extra_types": 2,
            "unclassified_count": 1,
            "confidence_threshold": 0.7
        }
        
        # Sample classified documents for testing
        self.classified_docs = [
            {
                "filename": "privacy_policy1.pdf",
                "content": "Privacy policy content...",
                "classification_result": {
                    "type_id": "privacy_policy",
                    "type_name": "Privacy Policy",
                    "confidence": 0.92,
                    "rationale": "Clear privacy policy content",
                    "evidence": ["We collect personal information", "Your privacy matters"]
                }
            },
            {
                "filename": "security_controls.pdf",
                "content": "Security policy content...",
                "classification_result": {
                    "type_id": "security_policy",
                    "type_name": "Security Policy",
                    "confidence": 0.85,
                    "rationale": "Contains security controls information",
                    "evidence": ["Access control measures", "Data encryption"]
                }
            },
            {
                "filename": "unknown1.pdf",
                "content": "Some content...",
                "classification_result": {
                    "type_id": "unknown",
                    "type_name": "Unknown",
                    "confidence": 0.45,
                    "rationale": "No clear match to any document type",
                    "evidence": ["Generic content"]
                }
            }
        ]
    
    def tearDown(self):
        """Clean up after each test"""
        self.temp_dir.cleanup()
    
    def test_initializer(self):
        """Test that the visualizer initializes correctly"""
        # Arrange & Act
        visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Assert
        self.assertEqual(visualizer.output_dir, self.output_dir)
        self.assertEqual(len(visualizer.generated_reports), 0)
    
    def test_generate_json_report(self):
        """Test generation of JSON report"""
        # Arrange
        visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Act
        json_content = visualizer._generate_json_report(self.verification_result, self.classified_docs)
        
        # Assert - validate JSON format
        report_data = json.loads(json_content)
        self.assertIn("report_type", report_data)
        self.assertIn("timestamp", report_data)
        self.assertIn("verification_result", report_data)
        self.assertIn("documents_by_type", report_data)
        self.assertIn("summary", report_data)
        
        # Check summary values
        self.assertEqual(report_data["summary"]["total_documents"], 6)
        self.assertEqual(report_data["summary"]["total_required_types"], 3)
        self.assertEqual(report_data["summary"]["total_found_required_types"], 2)
        self.assertEqual(report_data["summary"]["coverage_percentage"], 66.7)
    
    def test_generate_html_report(self):
        """Test generation of HTML report"""
        # Arrange
        visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Act
        html_content = visualizer._generate_html_report(self.verification_result, self.classified_docs)
        
        # Assert - validate HTML format and content
        self.assertIn("<!DOCTYPE html>", html_content)
        self.assertIn("<title>Document Classification Report</title>", html_content)
        
        # Check for key sections
        self.assertIn("Document Classification Report", html_content)
        self.assertIn("Summary", html_content)
        self.assertIn("Found Required Document Types", html_content)
        self.assertIn("Missing Required Document Types", html_content)
        
        # Check for specific content
        self.assertIn("Privacy Policy", html_content)
        self.assertIn("Security Policy", html_content)
        self.assertIn("Incident Response Plan", html_content)
        self.assertIn("66.7%", html_content)  # Coverage
    
    def test_generate_report_file_output(self):
        """Test that reports are written to files correctly"""
        # Arrange
        visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Act
        html_path = visualizer.generate_report(
            self.verification_result,
            self.classified_docs,
            format="html",
            filename="test_report"
        )
        
        json_path = visualizer.generate_report(
            self.verification_result,
            self.classified_docs,
            format="json",
            filename="test_report"
        )
        
        # Assert
        self.assertTrue(os.path.exists(html_path))
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(html_path.endswith(".html"))
        self.assertTrue(json_path.endswith(".json"))
        
        # Verify content of generated files
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            self.assertIn("<!DOCTYPE html>", html_content)
            self.assertIn("Document Classification Report", html_content)
        
        with open(json_path, 'r', encoding='utf-8') as f:
            json_content = f.read()
            report_data = json.loads(json_content)
            self.assertIn("verification_result", report_data)
    
    def test_generate_all_reports(self):
        """Test generation of all report formats at once"""
        # Arrange
        visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Act
        report_paths = visualizer.generate_all_reports(
            self.verification_result,
            self.classified_docs,
            base_filename="multi_format_test"
        )
        
        # Assert
        self.assertIn("html", report_paths)
        self.assertIn("json", report_paths)
        self.assertEqual(len(report_paths), 2)
        
        for path in report_paths.values():
            self.assertTrue(os.path.exists(path))
    
    def test_default_filenames(self):
        """Test that default filenames are generated with timestamps"""
        # Arrange
        visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Act
        html_path = visualizer.generate_report(
            self.verification_result,
            format="html"
        )
        
        # Assert
        self.assertIsNotNone(html_path)
        filename = os.path.basename(html_path)
        # Should contain "classification_report" and a timestamp format YYYYMMDD_HHMMSS
        self.assertRegex(filename, r"classification_report_\d{8}_\d{6}\.html")
    
    def test_no_classified_documents(self):
        """Test report generation without classified documents"""
        # Arrange
        visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Act
        html_content = visualizer._generate_html_report(self.verification_result)
        json_content = visualizer._generate_json_report(self.verification_result)
        
        # Assert
        self.assertIn("Document Classification Report", html_content)
        report_data = json.loads(json_content)
        self.assertIn("verification_result", report_data)
        self.assertNotIn("documents_by_type", report_data)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_file_write_error_handling(self, mock_mkdir, mock_file):
        """Test error handling when file writing fails"""
        # Arrange
        mock_file.side_effect = IOError("Simulated write error")
        visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Act
        result = visualizer.generate_report(
            self.verification_result,
            format="html",
            filename="error_test"
        )
        
        # Assert
        self.assertIsNone(result)
        self.assertEqual(len(visualizer.generated_reports), 0)
    
    def test_unsupported_format(self):
        """Test handling of unsupported report formats"""
        # Arrange
        visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Act
        result = visualizer.generate_report(
            self.verification_result,
            format="xml",  # Unsupported format
            filename="unsupported_test"
        )
        
        # Assert
        self.assertIsNone(result)
    
    def test_standalone_function(self):
        """Test the standalone generate_visualization_reports function"""
        # Arrange & Act
        report_paths = generate_visualization_reports(
            self.verification_result,
            self.classified_docs,
            output_dir=str(self.output_dir),
            formats=["html", "json"]
        )
        
        # Assert
        self.assertIn("html", report_paths)
        self.assertIn("json", report_paths)
        self.assertEqual(len(report_paths), 2)
        
        for path in report_paths.values():
            self.assertTrue(os.path.exists(path))
    
    def test_format_subset(self):
        """Test generating only a subset of formats"""
        # Arrange
        visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Act - only generate HTML
        result = generate_visualization_reports(
            self.verification_result,
            output_dir=str(self.output_dir),
            formats=["html"]
        )
        
        # Assert
        self.assertIn("html", result)
        self.assertNotIn("json", result)
        self.assertEqual(len(result), 1)

if __name__ == '__main__':
    unittest.main()