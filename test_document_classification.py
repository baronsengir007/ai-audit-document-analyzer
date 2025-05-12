#!/usr/bin/env python
"""
End-to-End Tests for TNO AI Audit Document Scanner

This module contains end-to-end tests that validate the core auditor use cases:
1. Regulatory Compliance Verification - Verifying that the system correctly identifies 
   missing required document types from a collection of documents
2. Audit Report Generation - Verifying that the system generates comprehensive reports
   showing coverage metrics, missing documents, and confidence levels

How to run these tests:
1. Using the test_runner.py:
   python test_runner.py --test-path=test_document_classification.py

2. Using pytest directly:
   pytest test_document_classification.py -v

How to interpret results:
- Success: Both tests pass, confirming the system properly supports the auditor use cases
- Failure: Error details will indicate which auditor use case is not properly supported
  and what specific aspect failed (identification of missing documents, report generation, etc.)

Dependencies:
- The tests use the test documents in the test_documents/ directory
- DocumentClassificationSystem from src.main
- The configuration in config/document_types.yaml
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import unittest
import pytest
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import system components
from src.main import DocumentClassificationSystem

# Configuration constants
TEST_INPUT_DIR = Path("test_documents")
REQUIRED_DOCUMENT_TYPES = [
    "privacy_policy", 
    "data_processing_agreement", 
    "security_policy", 
    "acceptable_use_policy", 
    "incident_response_plan"
]

# Mock LLM response data for consistent testing
MOCK_LLM_RESPONSES = {
    "privacy_policy": {
        "type_id": "privacy_policy",
        "type_name": "Privacy Policy",
        "confidence": 0.9,
        "evidence": ["We collect the following types of personal information", 
                    "Your data is processed according to the following principles"],
        "rationale": "This document outlines how user data is collected and processed"
    },
    "security_policy": {
        "type_id": "security_policy",
        "type_name": "Information Security Policy",
        "confidence": 0.85,
        "evidence": ["Access control measures", "Data shall be encrypted"],
        "rationale": "This document outlines security controls and practices"
    },
    "acceptable_use": {
        "type_id": "acceptable_use_policy",
        "type_name": "Acceptable Use Policy",
        "confidence": 0.87,
        "evidence": ["Company resources shall only be used for authorized business purposes",
                    "Employees shall not use company systems to access inappropriate content"],
        "rationale": "This document defines acceptable use of company IT resources"
    },
    "incident_response": {
        "type_id": "incident_response_plan",
        "type_name": "Incident Response Plan",
        "confidence": 0.88,
        "evidence": ["The incident response team shall be notified immediately",
                    "Incidents shall be categorized according to the following severity levels"],
        "rationale": "This document outlines procedures for responding to security incidents"
    },
    "dpa": {
        "type_id": "data_processing_agreement",
        "type_name": "Data Processing Agreement",
        "confidence": 0.86,
        "evidence": ["The Processor shall process the Personal Data only on documented instructions",
                    "The Processor shall implement appropriate technical and organizational measures"],
        "rationale": "This is a legal contract between data controller and processor"
    },
    "unknown": {
        "type_id": "unknown",
        "type_name": "Unknown Document Type",
        "confidence": 0.3,
        "evidence": [],
        "rationale": "The document does not match any known document types"
    }
}


class TestDocumentClassification(unittest.TestCase):
    """End-to-end tests for the document classification system, focused on auditor use cases."""

    def setUp(self):
        """
        Set up test environment before each test.
        
        Creates a temporary output directory, initializes the document classification system,
        and sets up LLM mocking for consistent test results.
        """
        # Create temporary output directory
        self.temp_output_dir = tempfile.mkdtemp()
        
        # Configuration directory
        self.config_dir = Path("config")
        
        # Initialize the document classification system with test directories
        self.system = DocumentClassificationSystem(
            input_dir=TEST_INPUT_DIR,
            output_dir=Path(self.temp_output_dir),
            config_dir=self.config_dir,
            confidence_threshold=0.7,
            use_cache=False  # Disable caching for predictable test behavior
        )
        
        # Setup LLM mocking
        self.setup_mocked_llm()
        
        # Print test environment information to help with debugging
        print(f"\nTest setup: Using test documents from {TEST_INPUT_DIR}")
        print(f"Temporary output directory: {self.temp_output_dir}")

    def tearDown(self):
        """
        Clean up after each test.
        
        Removes temporary output directory and stops LLM mocking to prevent
        test contamination.
        """
        # Remove temporary output directory
        shutil.rmtree(self.temp_output_dir, ignore_errors=True)
        
        # Stop LLM mocking
        if hasattr(self, 'llm_patcher'):
            self.llm_patcher.stop()

    def setup_mocked_llm(self):
        """
        Set up mocked LLM responses for consistent testing.
        
        Patches the OllamaWrapper.classify_text method to return predictable
        responses based on document content.
        """
        self.llm_patcher = patch('src.llm_wrapper.OllamaWrapper.classify_text')
        self.mock_llm = self.llm_patcher.start()
        self.mock_llm.side_effect = self._get_mock_response

    def _get_mock_response(self, text, prompt=None):
        """
        Return a mock LLM response based on document content.
        
        Args:
            text: The document text to classify
            prompt: Optional prompt text (ignored in mock)
            
        Returns:
            Dict containing classification response with type_id, confidence, etc.
        """
        # Check document content to determine the document type
        if "privacy" in text.lower() or "personal data" in text.lower():
            return MOCK_LLM_RESPONSES["privacy_policy"]
        elif "security" in text.lower() or "access control" in text.lower():
            return MOCK_LLM_RESPONSES["security_policy"]
        elif "acceptable use" in text.lower() or "company resources" in text.lower():
            return MOCK_LLM_RESPONSES["acceptable_use"]
        elif "incident response" in text.lower() or "security incident" in text.lower():
            return MOCK_LLM_RESPONSES["incident_response"]
        elif "processor" in text.lower() or "controller" in text.lower() or "dpa" in text.lower():
            return MOCK_LLM_RESPONSES["dpa"]
        else:
            return MOCK_LLM_RESPONSES["unknown"]

    # Helper functions for document filtering
    def _apply_document_filter(self, exclude_pattern):
        """
        Apply a document filter that excludes documents matching a pattern.
        
        Args:
            exclude_pattern: Pattern to exclude from document filenames
        """
        self.original_process_documents = self.system.process_documents
        
        def filtered_process_documents():
            documents = self.original_process_documents()
            
            # Filter out documents matching pattern
            filtered_docs = []
            for doc in documents:
                if exclude_pattern not in doc.get('filename', '').lower():
                    filtered_docs.append(doc)
            
            print(f"Filtered documents: {len(filtered_docs)} of {len(documents)} kept (excluding '{exclude_pattern}')")
            return filtered_docs
        
        self.system.process_documents = filtered_process_documents

    def _apply_document_filter_include_only(self, include_pattern):
        """
        Apply a document filter that includes only documents matching a pattern.
        
        Args:
            include_pattern: Pattern to include from document filenames
        """
        self.original_process_documents = self.system.process_documents
        
        def filtered_process_documents():
            documents = self.original_process_documents()
            
            # Filter to include only documents matching pattern
            filtered_docs = []
            for doc in documents:
                if include_pattern in doc.get('filename', '').lower():
                    filtered_docs.append(doc)
            
            print(f"Filtered documents: {len(filtered_docs)} of {len(documents)} kept (only '{include_pattern}')")
            return filtered_docs
        
        self.system.process_documents = filtered_process_documents

    def _restore_document_processing(self):
        """Restore original document processing function"""
        if hasattr(self, 'original_process_documents'):
            self.system.process_documents = self.original_process_documents

    # Helper functions for report validation
    def _read_report_content(self, report_path):
        """
        Read content from a report file.
        
        Args:
            report_path: Path to the report file
            
        Returns:
            Report content as string
        """
        with open(report_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _read_json_report(self, json_path):
        """
        Read and parse JSON report.
        
        Args:
            json_path: Path to the JSON report file
            
        Returns:
            Parsed JSON data as dictionary
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _extract_missing_type_ids(self, json_data):
        """
        Extract missing type IDs from JSON report.
        
        Args:
            json_data: Parsed JSON report data
            
        Returns:
            List of missing type IDs
        """
        if "verification_result" in json_data:
            missing_types = json_data["verification_result"].get("missing_types", [])
            return [item.get("id", "") for item in missing_types]
        return []

    def _validate_report_generation(self, report_paths):
        """
        Validate that reports were generated correctly.
        
        Args:
            report_paths: Dictionary of report paths by format
        """
        self.assertIn('html', report_paths, "HTML report should be generated")
        self.assertIn('json', report_paths, "JSON report should be generated")
        
        for format, path in report_paths.items():
            self.assertTrue(os.path.exists(path), f"{format.upper()} report file not found")
            self.assertTrue(os.path.getsize(path) > 0, f"{format.upper()} report file is empty")

    def _validate_html_report(self, html_path, verification_result):
        """
        Comprehensive validation of HTML report.
        
        Args:
            html_path: Path to HTML report
            verification_result: Verification result to validate against
        """
        html_content = self._read_report_content(html_path)
        
        # Check for dashboard metrics
        self.assertIn('<div class="dashboard">', html_content, 
                     "HTML report should include dashboard section")
        
        # Check for document types sections
        self.assertIn('Found Required Document Types', html_content,
                     "HTML report should include found document types section")
        self.assertIn('Missing Required Document Types', html_content,
                     "HTML report should include missing document types section")
        
        # Check for document details
        self.assertIn('Detailed Document Classification', html_content,
                     "HTML report should include detailed classification section")
        
        # Validate each found document type is represented
        for doc_type in verification_result.get('found_types', []):
            self.assertIn(doc_type['name'], html_content,
                         f"HTML report should include found document type: {doc_type['name']}")

    def _validate_json_report(self, json_path, verification_result):
        """
        Comprehensive validation of JSON report.
        
        Args:
            json_path: Path to JSON report
            verification_result: Verification result to validate against
        """
        json_data = self._read_json_report(json_path)
        
        # Check report structure
        self.assertIn('report_type', json_data, "JSON report missing report_type")
        self.assertIn('timestamp', json_data, "JSON report missing timestamp")
        self.assertIn('verification_result', json_data, "JSON report missing verification_result")
        self.assertIn('summary', json_data, "JSON report missing summary section")
        
        # Check summary metrics
        summary = json_data.get('summary', {})
        self.assertIn('total_documents', summary, "JSON summary missing total_documents")
        self.assertIn('coverage_percentage', summary, "JSON summary missing coverage_percentage")
        
        # Validate document counts
        doc_count = summary.get('total_documents', 0)
        self.assertEqual(doc_count, len(self.system.documents),
                        f"Document count in report ({doc_count}) doesn't match actual count")
        
        # Validate that verification_result matches expected result
        if 'found_types' in verification_result and 'found_types' in json_data.get('verification_result', {}):
            json_found_types = [t.get('id') for t in json_data['verification_result'].get('found_types', [])]
            expected_found_types = [t.get('id') for t in verification_result.get('found_types', [])]
            self.assertEqual(set(json_found_types), set(expected_found_types),
                           "Found document types in JSON don't match expected types")

    def _calculate_expected_metrics(self, documents, classified_documents):
        """
        Calculate expected metrics based on document set.
        
        Args:
            documents: List of processed documents
            classified_documents: List of classified documents
            
        Returns:
            Dictionary of expected metrics
        """
        total_documents = len(documents)
        
        # Count documents by type
        type_counts = {}
        for doc in classified_documents:
            if 'classification_result' in doc:
                type_id = doc['classification_result'].get('type_id', 'unknown')
                if type_id not in type_counts:
                    type_counts[type_id] = 0
                type_counts[type_id] += 1
                
        # Count required types found
        required_found = sum(1 for t in type_counts if t in REQUIRED_DOCUMENT_TYPES)
        total_required = len(REQUIRED_DOCUMENT_TYPES)
        missing_required = total_required - required_found
        
        # Calculate coverage
        coverage = required_found / total_required if total_required > 0 else 0
        
        return {
            'total_documents': total_documents,
            'required_found': required_found,
            'total_required': total_required,
            'missing_required': missing_required,
            'coverage': coverage,
            'type_counts': type_counts
        }

    def _validate_metrics(self, summary, expected_metrics):
        """
        Validate metrics in summary against expected values.
        
        Args:
            summary: Pipeline summary
            expected_metrics: Dictionary of expected metric values
        """
        self.assertEqual(
            summary.get('documents_processed', 0),
            expected_metrics['total_documents'],
            "Documents processed count doesn't match expected value"
        )
        
        self.assertEqual(
            summary.get('required_types_found', 0),
            expected_metrics['required_found'],
            "Required types found count doesn't match expected value"
        )
        
        self.assertEqual(
            summary.get('required_types_missing', 0),
            expected_metrics['missing_required'],
            "Required types missing count doesn't match expected value"
        )
        
        # Allow small floating point difference in coverage percentage
        expected_coverage = expected_metrics['coverage'] * 100
        actual_coverage = summary.get('coverage_percentage', 0)
        self.assertAlmostEqual(
            actual_coverage,
            expected_coverage,
            delta=0.1,  # Allow 0.1% difference
            msg="Coverage percentage doesn't match expected value"
        )

    def _validate_confidence_reporting(self, json_data):
        """
        Validate confidence score reporting in JSON data.
        
        Args:
            json_data: Parsed JSON report data
        """
        if "classified_documents" in json_data:
            for doc in json_data["classified_documents"]:
                if "classification_result" in doc:
                    self.assertIn("confidence", doc["classification_result"],
                                 "Document missing confidence score")
                    
                    confidence = doc["classification_result"]["confidence"]
                    self.assertGreaterEqual(confidence, 0.0,
                                          "Confidence should be at least 0.0")
                    self.assertLessEqual(confidence, 1.0,
                                       "Confidence should be at most 1.0")

    def _validate_report_structure(self, report_paths):
        """
        Validate overall report structure regardless of content.
        
        Args:
            report_paths: Dictionary of report paths by format
        """
        # HTML structure validation
        if 'html' in report_paths:
            html_content = self._read_report_content(report_paths['html'])
            # Check for basic HTML structure
            self.assertTrue(html_content.startswith('<!DOCTYPE html>'),
                           "HTML report should start with DOCTYPE declaration")
            self.assertIn('</html>', html_content,
                         "HTML report should have closing HTML tag")
        
        # JSON structure validation
        if 'json' in report_paths:
            try:
                json_data = self._read_json_report(report_paths['json'])
                # Check it's a dictionary with expected top-level keys
                self.assertIsInstance(json_data, dict,
                                    "JSON report should be a dictionary")
                for key in ['report_type', 'timestamp', 'verification_result', 'summary']:
                    self.assertIn(key, json_data, f"JSON report missing '{key}' section")
            except json.JSONDecodeError:
                self.fail("JSON report is not valid JSON")

    def test_identifies_missing_required_documents(self):
        """
        Test: Regulatory Compliance Verification Use Case
        
        This test verifies that the system correctly identifies missing required 
        document types from a collection of documents.
        
        Approach:
        1. Create a filter that excludes one or more required document types
        2. Run the document classification pipeline
        3. Verify that the system correctly identifies the missing document types
        
        This validates the primary auditor use case where they need to quickly
        identify which required documents are missing from a collection.
        """
        # Skip certain document types to simulate missing required documents
        # We'll modify the document loader's behavior for this test using a monkeypatch
        original_process_documents = self.system.process_documents
        
        def filtered_process_documents():
            """Modified document processor that excludes privacy_policy documents"""
            documents = original_process_documents()
            
            # Filter out privacy policy documents
            filtered_docs = []
            for doc in documents:
                # Skip any document with 'privacy' in the filename
                if 'privacy' not in doc.get('filename', '').lower():
                    filtered_docs.append(doc)
            
            print(f"Filtered documents: {len(filtered_docs)} of {len(documents)} kept")
            return filtered_docs
        
        # Apply the monkeypatch
        self.system.process_documents = filtered_process_documents
        
        try:
            # Run the pipeline
            summary = self.system.run_pipeline()
            
            # POSITIVE TEST: Verify that the system detected missing required documents
            self.assertLess(
                summary.get('coverage_percentage', 100), 
                100.0,
                "Missing document test failed: System should detect less than 100% coverage"
            )
            
            # NEGATIVE TEST: Verify correct identification of what's missing
            verification_result = self.system.verification_result
            
            # Verify that the missing types list is not empty
            self.assertTrue(
                len(verification_result.get('missing_types', [])) > 0,
                "Missing document test failed: 'missing_types' list should not be empty"
            )
            
            # Verify that 'privacy_policy' is in the missing types
            missing_type_ids = [item.get('id', '') for item in verification_result.get('missing_types', [])]
            self.assertIn(
                'privacy_policy', 
                missing_type_ids,
                "Missing document test failed: 'privacy_policy' should be identified as missing"
            )
            
            # Verify correct found documents (negative check)
            found_type_ids = [item.get('id', '') for item in verification_result.get('found_types', [])]
            self.assertNotIn(
                'privacy_policy',
                found_type_ids,
                "Missing document test failed: 'privacy_policy' incorrectly marked as found"
            )
            
            print(f"✅ Successfully identified missing documents with {summary.get('coverage_percentage', 0):.1f}% coverage")
            
        finally:
            # Restore original method
            self.system.process_documents = original_process_documents

    def test_audit_report_completeness(self):
        """
        Test: Audit Report Generation Use Case - Enhanced Version
        
        This test verifies that the system generates comprehensive reports showing
        coverage metrics, missing documents, and confidence levels.
        
        Approach:
        1. Run the document classification pipeline
        2. Verify that HTML and JSON reports are generated
        3. Validate that the reports contain all required information
        
        This validates the auditor use case where they need to include comprehensive
        document coverage reports in formal audit documentation.
        """
        # Run the pipeline
        summary = self.system.run_pipeline()
        
        # POSITIVE TEST: Verify reports were generated
        self.assertIn(
            'report_paths', 
            summary,
            "Audit report test failed: No report paths in summary"
        )
        self.assertTrue(
            len(summary.get('report_paths', {})) > 0,
            "Audit report test failed: No reports were generated"
        )
        
        # Get the report paths
        report_paths = summary.get('report_paths', {})
        
        # Enhanced validation: Verify report generation
        self._validate_report_generation(report_paths)
        
        # POSITIVE TEST: Check for HTML report
        if 'html' in report_paths:
            html_report_path = report_paths['html']
            self.assertTrue(
                os.path.exists(html_report_path),
                f"Audit report test failed: HTML report file not found at {html_report_path}"
            )
            
            # Check HTML report content
            with open(html_report_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
                # Verify the HTML contains essential elements
                essential_elements = [
                    "<!DOCTYPE html>",  # Basic HTML structure
                    "<html",
                    "<table",           # Should have tables for documents
                    "coverage",         # Should mention coverage
                    "confidence"        # Should include confidence values
                ]
                
                for element in essential_elements:
                    self.assertIn(
                        element,
                        html_content,
                        f"Audit report test failed: HTML report missing '{element}'"
                    )
                
                # Enhanced validation
                self._validate_html_report(html_report_path, self.system.verification_result)
                
                print(f"✅ HTML report validated at {html_report_path}")
        
        # POSITIVE TEST: Check for JSON report
        if 'json' in report_paths:
            json_report_path = report_paths['json']
            self.assertTrue(
                os.path.exists(json_report_path),
                f"Audit report test failed: JSON report file not found at {json_report_path}"
            )
            
            # Check JSON report content
            try:
                with open(json_report_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                    # POSITIVE TEST: Verify the JSON contains required keys
                    required_keys = [
                        "found_required_types",
                        "missing_types",
                        "coverage",
                        "classified_documents"
                    ]
                    
                    for key in required_keys:
                        self.assertIn(
                            key,
                            json_data,
                            f"Audit report test failed: JSON report missing '{key}' field"
                        )
                    
                    # Enhanced validation
                    self._validate_json_report(json_report_path, self.system.verification_result)
                    
                    # NEGATIVE TEST: Verify the JSON data is correctly structured
                    if "classified_documents" in json_data:
                        for doc in json_data["classified_documents"]:
                            self.assertIn(
                                "confidence",
                                doc.get("classification_result", {}),
                                "Audit report test failed: Document classification missing confidence score"
                            )
                            
                            # Verify confidence values are within valid range (negative check)
                            confidence = doc.get("classification_result", {}).get("confidence", 0)
                            self.assertGreaterEqual(
                                confidence, 
                                0.0,
                                f"Audit report test failed: Confidence value {confidence} is less than 0.0"
                            )
                            self.assertLessEqual(
                                confidence, 
                                1.0,
                                f"Audit report test failed: Confidence value {confidence} is greater than 1.0"
                            )
                    
                    print(f"✅ JSON report validated at {json_report_path}")
                    
            except json.JSONDecodeError:
                self.fail("Audit report test failed: JSON report is not valid JSON")
        
        # Validate metrics against expected values
        expected_metrics = self._calculate_expected_metrics(
            self.system.documents, 
            self.system.classified_documents
        )
        self._validate_metrics(summary, expected_metrics)
        
        # Summary validation
        self.assertIn(
            'coverage_percentage', 
            summary,
            "Audit report test failed: No coverage percentage in summary"
        )
        self.assertIn(
            'required_types_found', 
            summary,
            "Audit report test failed: No required types found count in summary"
        )
        self.assertIn(
            'required_types_missing', 
            summary,
            "Audit report test failed: No required types missing count in summary"
        )
        
        print(f"✅ Successfully generated and validated audit reports")

    def test_reports_with_missing_document_types(self):
        """
        Test: Report Generation with Missing Required Documents
        
        This test verifies that reports correctly reflect missing required document types.
        
        Approach:
        1. Filter documents to exclude privacy policy documents
        2. Run the classification pipeline
        3. Verify that reports correctly identify missing document types
        4. Validate coverage metrics reflect the missing documents
        
        This validates that reports accurately represent document coverage gaps.
        """
        # Apply document filter to exclude privacy policy documents
        self._apply_document_filter("privacy")
        
        try:
            # Run pipeline
            summary = self.system.run_pipeline()
            
            # Verify reports were generated
            self.assertIn('report_paths', summary, "No report paths in summary")
            report_paths = summary.get('report_paths', {})
            
            # Validate HTML report includes missing document section
            if 'html' in report_paths:
                html_content = self._read_report_content(report_paths['html'])
                
                # Check for missing documents section
                self.assertIn('Missing Required Document Types', html_content,
                             "HTML report should show Missing Required Document Types section")
                self.assertIn('Privacy Policy', html_content,
                             "HTML report should mention missing Privacy Policy")
                
                # Check that coverage is reflected correctly
                self.assertNotIn('coverage-good', html_content,
                               "HTML report should not show perfect coverage")
            
            # Validate JSON report correctly identifies missing documents
            if 'json' in report_paths:
                json_data = self._read_json_report(report_paths['json'])
                
                # Validate missing types
                missing_types = self._extract_missing_type_ids(json_data)
                self.assertIn('privacy_policy', missing_types,
                             "JSON report should identify 'privacy_policy' as missing")
                
                # Validate coverage is less than 100%
                if 'summary' in json_data:
                    coverage = json_data['summary'].get('coverage_percentage', 100)
                    self.assertLess(coverage, 100.0,
                                   "Coverage percentage should be less than 100%")
            
            # Validate expected metrics
            expected_metrics = self._calculate_expected_metrics(
                self.system.documents, 
                self.system.classified_documents
            )
            self._validate_metrics(summary, expected_metrics)
            
            # Specific checks for missing document scenario
            self.assertLess(
                summary.get('coverage_percentage', 100), 
                100.0,
                "Coverage should be less than 100% when documents are missing"
            )
            
            self.assertGreaterEqual(
                summary.get('required_types_missing', 0),
                1,
                "At least one required document type should be missing"
            )
            
            print(f"✅ Successfully validated reports with missing document types")
            
        finally:
            # Restore original document processing
            self._restore_document_processing()

    def test_reports_with_edge_cases(self):
        """
        Test: Report Generation with Edge Case Documents
        
        This test verifies that reports handle edge case documents appropriately.
        
        Approach:
        1. Filter documents to include only edge cases
        2. Run the classification pipeline
        3. Verify reports handle malformed documents gracefully
        4. Validate confidence scoring for ambiguous documents
        
        This validates the system's robustness when dealing with non-standard documents.
        """
        # Apply filter to include only edge case documents
        self._apply_document_filter_include_only("edge_cases")
        
        try:
            # Run pipeline
            summary = self.system.run_pipeline()
            
            # Verify reports were generated
            self.assertIn('report_paths', summary, "No report paths in summary")
            report_paths = summary.get('report_paths', {})
            
            # Validate that reports are properly structured regardless of content
            self._validate_report_structure(report_paths)
            
            # Validate HTML report handles edge cases
            if 'html' in report_paths:
                html_content = self._read_report_content(report_paths['html'])
                
                # Check for edge case documents
                edge_case_files = [
                    "malformed_document",
                    "empty_document",
                    "quarterly_report",
                    "mixed_compliance_policy",
                    "partial_password_policy"
                ]
                
                # At least one edge case should be mentioned
                found_edge_cases = any(case in html_content for case in edge_case_files)
                self.assertTrue(found_edge_cases, 
                               "HTML report should include at least one edge case document")
            
            # Validate JSON report - check confidence scores
            if 'json' in report_paths:
                json_data = self._read_json_report(report_paths['json'])
                self._validate_confidence_reporting(json_data)
                
                # Validate document counts
                if 'summary' in json_data:
                    doc_count = json_data['summary'].get('total_documents', 0)
                    self.assertGreater(doc_count, 0, "JSON report should include processed documents")
            
            print(f"✅ Successfully validated reports with edge case documents")
            
        finally:
            # Restore original document processing
            self._restore_document_processing()


if __name__ == "__main__":
    pytest.main(["-v", __file__])