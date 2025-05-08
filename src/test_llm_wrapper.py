"""
Unit tests for the llm_wrapper module.
Tests functionality of the OllamaWrapper class with mocked API responses.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import logging
import requests

from .llm_wrapper import OllamaWrapper

class TestOllamaWrapper(unittest.TestCase):
    """Test the OllamaWrapper class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.wrapper = OllamaWrapper(model="test-model")
        
        # Example document and document types for testing
        self.example_doc = {
            "filename": "example.pdf",
            "content": "This is a sample privacy policy document explaining how user data is handled."
        }
        
        self.example_types = [
            {
                "id": "privacy_policy",
                "name": "Privacy Policy",
                "description": "Document explaining how user data is collected and handled",
                "required": True
            },
            {
                "id": "security_policy",
                "name": "Security Policy",
                "description": "Document outlining security measures",
                "required": True
            }
        ]
        
        # Configure logging to avoid polluting test output
        logging.getLogger("llm_wrapper").setLevel(logging.CRITICAL)
    
    @patch('requests.post')
    def test_make_request(self, mock_post):
        """Test _make_request method with successful API call"""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "test response"}
        mock_post.return_value = mock_response
        
        # Call method
        result = self.wrapper._make_request("test prompt", "test system prompt")
        
        # Verify request was made with correct parameters
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        self.assertEqual(call_args['json']['model'], "test-model")
        self.assertEqual(call_args['json']['prompt'], "test prompt")
        self.assertEqual(call_args['json']['system'], "test system prompt")
        
        # Verify result
        self.assertEqual(result, {"response": "test response"})
    
    @patch('requests.post')
    def test_make_request_timeout(self, mock_post):
        """Test _make_request method with timeout"""
        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        
        # Call method and verify exception
        with self.assertRaises(TimeoutError):
            self.wrapper._make_request("test prompt")
    
    @patch('requests.post')
    def test_make_request_connection_error(self, mock_post):
        """Test _make_request method with connection error"""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection Error")
        
        # Call method and verify exception
        with self.assertRaises(ConnectionError):
            self.wrapper._make_request("test prompt")
    
    def test_extract_json_from_text_direct(self):
        """Test extract_json_from_text with direct JSON"""
        # Test with direct JSON
        json_text = '{"type_id": "test", "confidence": 0.9}'
        result = self.wrapper.extract_json_from_text(json_text)
        self.assertEqual(result, {"type_id": "test", "confidence": 0.9})
    
    def test_extract_json_from_text_embedded(self):
        """Test extract_json_from_text with embedded JSON"""
        # Test with embedded JSON
        json_text = 'Some text before {"type_id": "test", "confidence": 0.9} and after'
        result = self.wrapper.extract_json_from_text(json_text)
        self.assertEqual(result, {"type_id": "test", "confidence": 0.9})
    
    def test_extract_json_from_text_array(self):
        """Test extract_json_from_text with JSON array"""
        # Test with JSON array
        json_text = 'Array: [{"id": "1"}, {"id": "2"}]'
        result = self.wrapper.extract_json_from_text(json_text)
        self.assertEqual(result, [{"id": "1"}, {"id": "2"}])
    
    def test_extract_json_from_text_invalid(self):
        """Test extract_json_from_text with invalid JSON"""
        # Test with invalid JSON
        json_text = 'Not JSON at all'
        with self.assertRaises(ValueError):
            self.wrapper.extract_json_from_text(json_text)
    
    def test_validate_classification_result_complete(self):
        """Test _validate_classification_result with complete result"""
        # Test with complete result
        result = {
            "type_id": "test",
            "type_name": "Test Type",
            "confidence": 0.9,
            "rationale": "Test rationale",
            "evidence": ["evidence1", "evidence2"]
        }
        
        validated = self.wrapper._validate_classification_result(result)
        self.assertEqual(validated, result)
    
    def test_validate_classification_result_missing_fields(self):
        """Test _validate_classification_result with missing fields"""
        # Test with missing fields
        result = {
            "type_id": "test"
        }
        
        validated = self.wrapper._validate_classification_result(result)
        self.assertEqual(validated["type_id"], "test")
        self.assertEqual(validated["type_name"], "unknown")
        self.assertEqual(validated["confidence"], 0.0)
        self.assertEqual(validated["rationale"], "unknown")
        self.assertEqual(validated["evidence"], [])
    
    def test_validate_classification_result_invalid_confidence(self):
        """Test _validate_classification_result with invalid confidence"""
        # Test with invalid confidence
        result = {
            "type_id": "test",
            "type_name": "Test Type",
            "confidence": "high",
            "rationale": "Test rationale",
            "evidence": ["evidence1"]
        }
        
        validated = self.wrapper._validate_classification_result(result)
        self.assertEqual(validated["confidence"], 0.0)
    
    def test_validate_classification_result_out_of_range_confidence(self):
        """Test _validate_classification_result with out-of-range confidence"""
        # Test with out-of-range confidence
        result = {
            "type_id": "test",
            "type_name": "Test Type",
            "confidence": 2.5,
            "rationale": "Test rationale",
            "evidence": ["evidence1"]
        }
        
        validated = self.wrapper._validate_classification_result(result)
        self.assertEqual(validated["confidence"], 1.0)
        
        # Test negative confidence
        result["confidence"] = -0.5
        validated = self.wrapper._validate_classification_result(result)
        self.assertEqual(validated["confidence"], 0.0)
    
    def test_validate_classification_result_non_list_evidence(self):
        """Test _validate_classification_result with non-list evidence"""
        # Test with non-list evidence
        result = {
            "type_id": "test",
            "type_name": "Test Type",
            "confidence": 0.9,
            "rationale": "Test rationale",
            "evidence": "single evidence"
        }
        
        validated = self.wrapper._validate_classification_result(result)
        self.assertEqual(validated["evidence"], ["single evidence"])
    
    @patch.object(OllamaWrapper, '_make_request')
    def test_classify_document_success(self, mock_make_request):
        """Test classify_document with successful response"""
        # Mock successful response
        mock_response = {
            "response": json.dumps({
                "type_id": "privacy_policy",
                "type_name": "Privacy Policy",
                "confidence": 0.95,
                "rationale": "The document discusses handling user data",
                "evidence": ["user data is handled"]
            })
        }
        mock_make_request.return_value = mock_response
        
        # Call method
        result = self.wrapper.classify_document(self.example_doc, self.example_types)
        
        # Verify result
        self.assertEqual(result["type_id"], "privacy_policy")
        self.assertEqual(result["type_name"], "Privacy Policy")
        self.assertEqual(result["confidence"], 0.95)
        self.assertIsInstance(result["evidence"], list)
    
    @patch.object(OllamaWrapper, '_make_request')
    def test_classify_document_empty_content(self, mock_make_request):
        """Test classify_document with empty document content"""
        # Create document with empty content
        empty_doc = {"filename": "empty.pdf", "content": ""}
        
        # Call method (should not call _make_request)
        result = self.wrapper.classify_document(empty_doc, self.example_types)
        
        # Verify default result
        self.assertEqual(result["type_id"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
        mock_make_request.assert_not_called()
    
    @patch.object(OllamaWrapper, '_make_request')
    def test_classify_document_no_types(self, mock_make_request):
        """Test classify_document with no document types"""
        # Call method with empty types list
        result = self.wrapper.classify_document(self.example_doc, [])
        
        # Verify default result
        self.assertEqual(result["type_id"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
        mock_make_request.assert_not_called()
    
    @patch.object(OllamaWrapper, '_make_request')
    def test_classify_document_json_error(self, mock_make_request):
        """Test classify_document with invalid JSON response"""
        # Mock invalid JSON response
        mock_response = {"response": "Not a valid JSON"}
        mock_make_request.return_value = mock_response
        
        # Call method
        result = self.wrapper.classify_document(self.example_doc, self.example_types)
        
        # Verify default result
        self.assertEqual(result["type_id"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("Error parsing LLM response", result["rationale"])
    
    @patch.object(OllamaWrapper, '_make_request')
    def test_classify_document_api_error(self, mock_make_request):
        """Test classify_document with API error"""
        # Mock API error
        mock_make_request.side_effect = Exception("API Error")
        
        # Call method
        result = self.wrapper.classify_document(self.example_doc, self.example_types)
        
        # Verify default result
        self.assertEqual(result["type_id"], "unknown")
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("Error during classification", result["rationale"])
    
    @patch.object(OllamaWrapper, '_make_request')
    def test_analyze_document(self, mock_make_request):
        """Test analyze_document method"""
        # Mock response
        mock_response = {
            "response": json.dumps({
                "satisfied": True,
                "explanation": "Document satisfies the checklist item",
                "found_keywords": ["keyword1"],
                "missing_keywords": []
            })
        }
        mock_make_request.return_value = mock_response
        
        # Create test document and checklist
        doc = {"filename": "test.pdf", "content": "Test content with keyword1"}
        checklist = {"id": "test_check", "description": "Test checklist", "required_keywords": ["keyword1"]}
        
        # Call method
        result = self.wrapper.analyze_document(doc, checklist)
        
        # Verify result
        self.assertTrue(result["satisfied"])
        self.assertEqual(result["found_keywords"], ["keyword1"])
        self.assertEqual(result["missing_keywords"], [])
    
    @patch.object(OllamaWrapper, '_make_request')
    def test_extract_policy_requirements(self, mock_make_request):
        """Test extract_policy_requirements method"""
        # Mock response
        mock_response = {
            "response": json.dumps([
                {
                    "id": "req_1",
                    "description": "Requirement 1",
                    "required_keywords": ["keyword1"]
                }
            ])
        }
        mock_make_request.return_value = mock_response
        
        # Create test document
        doc = {"filename": "policy.pdf", "content": "Test policy content"}
        
        # Call method
        result = self.wrapper.extract_policy_requirements(doc)
        
        # Verify result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "req_1")
        self.assertEqual(result[0]["description"], "Requirement 1")
        self.assertEqual(result[0]["required_keywords"], ["keyword1"])


if __name__ == "__main__":
    unittest.main()