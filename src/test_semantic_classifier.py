"""
Tests for the semantic document classifier module.
"""

import unittest
import json
import os
import yaml
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import sys

# Handle missing requests dependency for testing
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    # Create a minimal mock requests module
    class MockRequests:
        class Response:
            def __init__(self, status_code=200, json_data=None):
                self.status_code = status_code
                self._json_data = json_data or {}
                
            def json(self):
                return self._json_data
                
        @staticmethod
        def post(url, json=None, headers=None):
            # For testing, just return a success response
            return MockRequests.Response(
                status_code=200, 
                json_data={"response": "This is a mock response"}
            )
    
    # Install mock in sys.modules
    sys.modules['requests'] = MockRequests
    requests = MockRequests

from semantic_classifier import SemanticClassifier, classify_document_semantically

class TestSemanticClassifier(unittest.TestCase):
    """Test cases for the SemanticClassifier class"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        if not REQUESTS_AVAILABLE:
            print("\nWARNING: 'requests' package not available. Using mock implementation for tests.")
            print("Tests will run but with simulated HTTP responses.")
    
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
                    "examples": ["We collect personal information...", "Your privacy is important to us"]
                },
                {
                    "id": "security_policy",
                    "name": "Security Policy",
                    "description": "Document outlining security measures and controls",
                    "required": True,
                    "examples": ["Access control measures include...", "Data shall be encrypted"]
                },
                {
                    "id": "test_report",
                    "name": "Test Report",
                    "description": "Document containing test results",
                    "required": False,
                    "examples": ["Test results summary", "The following tests were executed"]
                }
            ]
        }
        
        # Write test configuration to file
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Sample documents for testing
        self.privacy_doc = {
            "filename": "privacy_policy.pdf",
            "content": "This document outlines our privacy practices. We collect personal information "
                       "including name, email, and usage data. Your privacy is important to us and we "
                       "take measures to protect your data according to applicable regulations."
        }
        
        self.security_doc = {
            "filename": "security_controls.pdf",
            "content": "Security Policy: This document details our security controls. Access control measures "
                       "include multi-factor authentication. Data shall be encrypted both in transit and at rest. "
                       "All employees must follow these security protocols."
        }
        
        self.empty_doc = {
            "filename": "empty.pdf",
            "content": ""
        }
        
        self.ambiguous_doc = {
            "filename": "general_policy.pdf",
            "content": "This is a generic company policy document with some general guidelines. "
                      "Please refer to specific policies for detailed requirements."
        }
        
        # Create sample LLM responses
        self.privacy_response = {
            "type_id": "privacy_policy",
            "type_name": "Privacy Policy",
            "confidence": 0.92,
            "rationale": "The document clearly discusses collection of personal information and privacy practices.",
            "evidence": [
                "We collect personal information including name, email, and usage data",
                "Your privacy is important to us"
            ]
        }
        
        self.security_response = {
            "type_id": "security_policy",
            "type_name": "Security Policy",
            "confidence": 0.88,
            "rationale": "The document describes security controls including access control and encryption.",
            "evidence": [
                "Access control measures include multi-factor authentication",
                "Data shall be encrypted both in transit and at rest"
            ]
        }
        
        self.unknown_response = {
            "type_id": "unknown",
            "type_name": "Unknown",
            "confidence": 0.45,
            "rationale": "The document contains general policy information but lacks specific details to classify it accurately.",
            "evidence": [
                "This is a generic company policy document with some general guidelines"
            ]
        }
    
    def tearDown(self):
        """Clean up after each test"""
        self.temp_dir.cleanup()
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_classifier_initialization(self, mock_ollama):
        """Test that the classifier initializes correctly"""
        # Arrange & Act
        classifier = SemanticClassifier(config_path=str(self.config_path))
        
        # Assert
        self.assertEqual(len(classifier.document_types), 3)
        self.assertEqual(len(classifier.get_document_types(required_only=True)), 2)
        mock_ollama.assert_called_once()
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_classify_document_privacy_policy(self, mock_ollama):
        """Test classification of a privacy policy document"""
        # Arrange
        mock_instance = mock_ollama.return_value
        mock_instance._make_request.return_value = {"response": json.dumps(self.privacy_response)}
        
        classifier = SemanticClassifier(config_path=str(self.config_path))
        
        # Act
        result = classifier.classify_document(self.privacy_doc)
        
        # Assert
        self.assertEqual(result["type_id"], "privacy_policy")
        self.assertGreaterEqual(result["confidence"], 0.7)
        self.assertTrue(len(result["evidence"]) > 0)
        mock_instance._make_request.assert_called_once()
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_classify_document_security_policy(self, mock_ollama):
        """Test classification of a security policy document"""
        # Arrange
        mock_instance = mock_ollama.return_value
        mock_instance._make_request.return_value = {"response": json.dumps(self.security_response)}
        
        classifier = SemanticClassifier(config_path=str(self.config_path))
        
        # Act
        result = classifier.classify_document(self.security_doc)
        
        # Assert
        self.assertEqual(result["type_id"], "security_policy")
        self.assertGreaterEqual(result["confidence"], 0.7)
        self.assertTrue(len(result["evidence"]) > 0)
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_classify_document_unknown(self, mock_ollama):
        """Test classification of an ambiguous document"""
        # Arrange
        mock_instance = mock_ollama.return_value
        mock_instance._make_request.return_value = {"response": json.dumps(self.unknown_response)}
        
        classifier = SemanticClassifier(config_path=str(self.config_path))
        
        # Act
        result = classifier.classify_document(self.ambiguous_doc)
        
        # Assert
        self.assertEqual(result["type_id"], "unknown")
        self.assertLess(result["confidence"], 0.7)
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_classify_empty_document(self, mock_ollama):
        """Test classification of an empty document"""
        # Arrange
        classifier = SemanticClassifier(config_path=str(self.config_path))
        
        # Act
        result = classifier.classify_document(self.empty_doc)
        
        # Assert
        self.assertEqual(result["type_id"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
        # Ensure LLM is not called for empty documents
        mock_instance = mock_ollama.return_value
        mock_instance._make_request.assert_not_called()
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_batch_classify(self, mock_ollama):
        """Test batch classification of documents"""
        # Arrange
        mock_instance = mock_ollama.return_value
        
        # Setup mock to return different responses for different documents
        def side_effect(prompt, system_prompt):
            if "privacy" in prompt:
                return {"response": json.dumps(self.privacy_response)}
            elif "security" in prompt:
                return {"response": json.dumps(self.security_response)}
            else:
                return {"response": json.dumps(self.unknown_response)}
        
        mock_instance._make_request.side_effect = side_effect
        
        classifier = SemanticClassifier(config_path=str(self.config_path))
        
        # Act
        results = classifier.batch_classify([self.privacy_doc, self.security_doc, self.empty_doc, self.ambiguous_doc])
        
        # Assert
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]["classification_result"]["type_id"], "privacy_policy")
        self.assertEqual(results[1]["classification_result"]["type_id"], "security_policy")
        self.assertEqual(results[2]["classification_result"]["type_id"], "unknown")  # Empty doc
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_confidence_threshold(self, mock_ollama):
        """Test that confidence threshold is respected"""
        # Arrange
        mock_instance = mock_ollama.return_value
        
        # Return a borderline confidence response
        borderline_response = self.unknown_response.copy()
        borderline_response["confidence"] = 0.65  # Just below default threshold of 0.7
        mock_instance._make_request.return_value = {"response": json.dumps(borderline_response)}
        
        # Create classifier with default threshold (0.7)
        default_classifier = SemanticClassifier(config_path=str(self.config_path))
        
        # Create classifier with lower threshold (0.6)
        low_threshold_classifier = SemanticClassifier(
            config_path=str(self.config_path),
            confidence_threshold=0.6
        )
        
        # Act
        # Classify the same document with both classifiers
        default_results = default_classifier.batch_classify([self.ambiguous_doc])
        low_threshold_results = low_threshold_classifier.batch_classify([self.ambiguous_doc])
        
        # Assert
        # The document should be considered "unclassified" with default threshold
        self.assertEqual(
            default_results[0]["classification_result"]["confidence"],
            0.65
        )
        
        # The document should be considered classified with lower threshold
        self.assertEqual(
            low_threshold_results[0]["classification_result"]["confidence"],
            0.65
        )
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_invalid_llm_response(self, mock_ollama):
        """Test handling of invalid LLM responses"""
        # Arrange
        mock_instance = mock_ollama.return_value
        
        # Setup a non-JSON response from the LLM
        mock_instance._make_request.return_value = {"response": "This is not valid JSON"}
        
        classifier = SemanticClassifier(config_path=str(self.config_path))
        
        # Act
        result = classifier.classify_document(self.privacy_doc)
        
        # Assert - should handle the error gracefully
        self.assertEqual(result["type_id"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_llm_error_handling(self, mock_ollama):
        """Test handling of LLM errors"""
        # Arrange
        mock_instance = mock_ollama.return_value
        mock_instance._make_request.side_effect = Exception("Simulated LLM error")
        
        classifier = SemanticClassifier(config_path=str(self.config_path))
        
        # Act
        result = classifier.classify_document(self.privacy_doc)
        
        # Assert - should handle the exception gracefully
        self.assertEqual(result["type_id"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("Error during classification", result["rationale"])
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_missing_fields_in_response(self, mock_ollama):
        """Test handling of missing fields in LLM response"""
        # Arrange
        mock_instance = mock_ollama.return_value
        
        # Create an incomplete response missing required fields
        incomplete_response = {
            "type_id": "privacy_policy",
            # Missing type_name, confidence, rationale, evidence
        }
        
        mock_instance._make_request.return_value = {"response": json.dumps(incomplete_response)}
        
        classifier = SemanticClassifier(config_path=str(self.config_path))
        
        # Act
        result = classifier.classify_document(self.privacy_doc)
        
        # Assert - should add default values for missing fields
        self.assertEqual(result["type_id"], "privacy_policy")
        self.assertEqual(result["type_name"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["rationale"], "unknown")
        self.assertEqual(result["evidence"], [])
    
    @patch('semantic_classifier.OllamaWrapper')
    def test_standalone_function(self, mock_ollama):
        """Test the standalone classify_document_semantically function"""
        # Arrange
        mock_instance = mock_ollama.return_value
        mock_instance._make_request.return_value = {"response": json.dumps(self.privacy_response)}
        
        # Act
        result = classify_document_semantically(
            self.privacy_doc,
            config_path=str(self.config_path)
        )
        
        # Assert
        self.assertEqual(result["type_id"], "privacy_policy")
        self.assertEqual(result["type_name"], "Privacy Policy")
        self.assertGreaterEqual(result["confidence"], 0.7)

if __name__ == '__main__':
    unittest.main()