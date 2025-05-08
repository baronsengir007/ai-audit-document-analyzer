"""
Tests for the type verification module.
"""

import unittest
import json
import os
import yaml
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from type_verification import TypeVerification, verify_document_types

class TestTypeVerification(unittest.TestCase):
    """Test cases for the TypeVerification class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create temporary test configuration
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
        self.config_path = self.config_dir / "test_document_types.yaml"
        
        # Sample document types configuration
        test_config = {
            "document_types": [
                {
                    "id": "privacy_policy",
                    "name": "Privacy Policy",
                    "description": "Document explaining how user data is collected and protected",
                    "required": True,
                },
                {
                    "id": "security_policy",
                    "name": "Security Policy",
                    "description": "Document outlining security measures and controls",
                    "required": True,
                },
                {
                    "id": "incident_response",
                    "name": "Incident Response Plan",
                    "description": "Document detailing response procedures for security incidents",
                    "required": True,
                },
                {
                    "id": "test_report",
                    "name": "Test Report",
                    "description": "Document containing test results",
                    "required": False,
                }
            ]
        }
        
        # Write test configuration to file
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Sample classified documents for testing
        self.classified_docs = [
            {
                "filename": "privacy_policy.pdf",
                "content": "Privacy policy content...",
                "classification_result": {
                    "type_id": "privacy_policy",
                    "type_name": "Privacy Policy",
                    "confidence": 0.92,
                    "rationale": "Clear privacy policy content",
                    "evidence": ["Evidence 1", "Evidence 2"]
                }
            },
            {
                "filename": "security_controls.pdf",
                "content": "Security policy content...",
                "classification_result": {
                    "type_id": "security_policy",
                    "type_name": "Security Policy",
                    "confidence": 0.88,
                    "rationale": "Clear security policy content",
                    "evidence": ["Evidence 1", "Evidence 2"]
                }
            },
            {
                "filename": "test_results.pdf",
                "content": "Test report content...",
                "classification_result": {
                    "type_id": "test_report",
                    "type_name": "Test Report",
                    "confidence": 0.85,
                    "rationale": "Contains test results",
                    "evidence": ["Evidence 1", "Evidence 2"]
                }
            },
            {
                "filename": "unknown_doc.pdf",
                "content": "Some content that doesn't match any type...",
                "classification_result": {
                    "type_id": "unknown",
                    "type_name": "Unknown",
                    "confidence": 0.45,
                    "rationale": "No clear match to any document type",
                    "evidence": ["Evidence 1"]
                }
            },
            {
                "filename": "low_confidence.pdf",
                "content": "Content with ambiguous classification...",
                "classification_result": {
                    "type_id": "privacy_policy",
                    "type_name": "Privacy Policy",
                    "confidence": 0.65,  # Below default threshold
                    "rationale": "Some privacy related content but not clear",
                    "evidence": ["Evidence 1"]
                }
            }
        ]
    
    def tearDown(self):
        """Clean up after each test"""
        self.temp_dir.cleanup()
    
    def test_verifier_initialization(self):
        """Test that the verifier initializes correctly"""
        # Arrange & Act
        verifier = TypeVerification(config_path=str(self.config_path))
        
        # Assert
        self.assertEqual(len(verifier.document_types), 4)
        self.assertEqual(len(verifier.required_types), 3)
    
    def test_verify_documents(self):
        """Test verification of classified documents"""
        # Arrange
        verifier = TypeVerification(config_path=str(self.config_path))
        
        # Act
        result = verifier.verify_documents(self.classified_docs)
        
        # Assert
        self.assertEqual(len(result["found_types"]), 2)  # privacy_policy, security_policy
        self.assertEqual(len(result["missing_types"]), 1)  # incident_response
        self.assertEqual(len(result["extra_types"]), 2)  # test_report, unknown
        self.assertAlmostEqual(result["coverage"], 2/3)  # 2 of 3 required types found
    
    def test_confidence_threshold(self):
        """Test that confidence threshold is respected"""
        # Arrange
        high_threshold_verifier = TypeVerification(
            config_path=str(self.config_path),
            confidence_threshold=0.9  # Only the privacy policy exceeds this
        )
        
        low_threshold_verifier = TypeVerification(
            config_path=str(self.config_path),
            confidence_threshold=0.6  # Includes low confidence privacy policy
        )
        
        # Act
        high_threshold_result = high_threshold_verifier.verify_documents(self.classified_docs)
        low_threshold_result = low_threshold_verifier.verify_documents(self.classified_docs)
        
        # Assert
        # High threshold: only privacy_policy should be found
        self.assertEqual(len(high_threshold_result["found_types"]), 1)
        self.assertEqual(high_threshold_result["found_types"][0]["id"], "privacy_policy")
        self.assertEqual(len(high_threshold_result["missing_types"]), 2)  # security_policy, incident_response
        
        # Low threshold: privacy_policy, security_policy, and low confidence doc should be counted
        self.assertEqual(len(low_threshold_result["found_types"]), 2)
        self.assertEqual(len(low_threshold_result["missing_types"]), 1)  # incident_response only
    
    def test_unclassified_documents(self):
        """Test handling of unclassified documents"""
        # Arrange
        verifier = TypeVerification(config_path=str(self.config_path))
        
        # Act
        result = verifier.verify_documents(self.classified_docs)
        
        # Assert
        self.assertEqual(len(result["unclassified_documents"]), 2)  # unknown and low confidence docs
    
    def test_empty_document_list(self):
        """Test verification with empty document list"""
        # Arrange
        verifier = TypeVerification(config_path=str(self.config_path))
        
        # Act
        result = verifier.verify_documents([])
        
        # Assert
        self.assertEqual(len(result["found_types"]), 0)
        self.assertEqual(len(result["missing_types"]), 3)  # All required types are missing
        self.assertEqual(result["coverage"], 0.0)
    
    def test_documents_by_type(self):
        """Test the documents_by_type grouping"""
        # Arrange
        verifier = TypeVerification(config_path=str(self.config_path))
        
        # Act
        result = verifier.verify_documents(self.classified_docs)
        
        # Assert
        self.assertIn("privacy_policy", result["documents_by_type"])
        self.assertIn("security_policy", result["documents_by_type"])
        self.assertIn("test_report", result["documents_by_type"])
        self.assertIn("unknown", result["documents_by_type"])
        
        # Check document counts
        self.assertEqual(len(result["documents_by_type"]["privacy_policy"]), 1)
        self.assertEqual(len(result["documents_by_type"]["security_policy"]), 1)
        self.assertEqual(len(result["documents_by_type"]["test_report"]), 1)
        self.assertEqual(len(result["documents_by_type"]["unknown"]), 1)
    
    def test_missing_types_summary(self):
        """Test generation of missing types summary"""
        # Arrange
        verifier = TypeVerification(config_path=str(self.config_path))
        verification_result = verifier.verify_documents(self.classified_docs)
        
        # Act
        summary = verifier.get_missing_types_summary(verification_result)
        
        # Assert
        self.assertIn("Missing 1 required document types", summary)
        self.assertIn("Incident Response Plan", summary)
    
    def test_no_missing_types_summary(self):
        """Test missing types summary when no types are missing"""
        # Arrange
        verifier = TypeVerification(config_path=str(self.config_path))
        
        # Add the missing incident response document
        complete_docs = self.classified_docs.copy()
        complete_docs.append({
            "filename": "incident_response.pdf",
            "content": "Incident response content...",
            "classification_result": {
                "type_id": "incident_response",
                "type_name": "Incident Response Plan",
                "confidence": 0.95,
                "rationale": "Clear incident response content",
                "evidence": ["Evidence 1", "Evidence 2"]
            }
        })
        
        verification_result = verifier.verify_documents(complete_docs)
        
        # Act
        summary = verifier.get_missing_types_summary(verification_result)
        
        # Assert
        self.assertEqual(summary, "All required document types are present.")
    
    def test_verification_report_text(self):
        """Test generation of text verification report"""
        # Arrange
        verifier = TypeVerification(config_path=str(self.config_path))
        verification_result = verifier.verify_documents(self.classified_docs)
        
        # Act
        report = verifier.generate_verification_report(verification_result, "text")
        
        # Assert
        self.assertIn("Document Type Verification Report", report)
        self.assertIn("Coverage: 66.7%", report)
        self.assertIn("Privacy Policy", report)
        self.assertIn("Security Policy", report)
        self.assertIn("Missing Required Document Types", report)
        self.assertIn("Incident Response Plan", report)
    
    def test_verification_report_markdown(self):
        """Test generation of markdown verification report"""
        # Arrange
        verifier = TypeVerification(config_path=str(self.config_path))
        verification_result = verifier.verify_documents(self.classified_docs)
        
        # Act
        report = verifier.generate_verification_report(verification_result, "markdown")
        
        # Assert
        self.assertIn("# Document Type Verification Report", report)
        self.assertIn("## Found Required Document Types", report)
        self.assertIn("* Privacy Policy", report)
        self.assertIn("* Security Policy", report)
    
    def test_verification_report_json(self):
        """Test generation of JSON verification report"""
        # Arrange
        verifier = TypeVerification(config_path=str(self.config_path))
        verification_result = verifier.verify_documents(self.classified_docs)
        
        # Act
        json_report = verifier.generate_verification_report(verification_result, "json")
        
        # Assert - should be valid JSON
        parsed_report = json.loads(json_report)
        self.assertEqual(parsed_report, verification_result)
    
    def test_standalone_function(self):
        """Test the standalone verify_document_types function"""
        # Act
        result = verify_document_types(
            self.classified_docs,
            config_path=str(self.config_path)
        )
        
        # Assert
        self.assertEqual(len(result["found_types"]), 2)
        self.assertEqual(len(result["missing_types"]), 1)
        self.assertEqual(len(result["extra_types"]), 2)

if __name__ == '__main__':
    unittest.main()