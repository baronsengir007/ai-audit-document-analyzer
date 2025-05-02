import unittest
import json
import logging
from json_parser import LLMResponseParser, ResponseType, ParserMetadata

class TestLLMResponseParser(unittest.TestCase):
    def setUp(self):
        self.parser = LLMResponseParser()
        logging.basicConfig(level=logging.INFO)
    
    def test_completeness_check_parsing(self):
        """Test parsing of completeness check response"""
        response = """
        {
            "satisfied": true,
            "explanation": "All required keywords found",
            "found_keywords": ["invoice", "date"],
            "missing_keywords": [],
            "confidence_score": 0.95,
            "suggestions": ["Add more detail"]
        }
        """
        data, metadata = self.parser.parse_response(response, ResponseType.COMPLETENESS_CHECK)
        self.assertTrue(data["satisfied"])
        self.assertEqual(len(data["found_keywords"]), 2)
        self.assertEqual(metadata.response_type, ResponseType.COMPLETENESS_CHECK)
    
    def test_required_fields_parsing(self):
        """Test parsing of required fields response"""
        response = """
        {
            "missing_fields": [],
            "present_fields": ["field1", "field2"],
            "field_details": [
                {
                    "field_name": "field1",
                    "is_present": true,
                    "location": "header",
                    "value": "test",
                    "confidence": 0.9
                }
            ],
            "overall_completeness": 1.0,
            "suggestions": []
        }
        """
        data, metadata = self.parser.parse_response(response, ResponseType.REQUIRED_FIELDS)
        self.assertEqual(len(data["present_fields"]), 2)
        self.assertEqual(data["overall_completeness"], 1.0)
    
    def test_type_specific_parsing(self):
        """Test parsing of type-specific response"""
        response = """
        {
            "satisfied": true,
            "completeness_score": 0.95,
            "keyword_analysis": {
                "found": ["keyword1"],
                "missing": []
            },
            "field_analysis": [
                {
                    "field_name": "field1",
                    "is_present": true,
                    "value": "test",
                    "format_valid": true,
                    "confidence": 0.9
                }
            ],
            "suggestions": [
                {
                    "field": "field1",
                    "issue": "brief",
                    "recommendation": "add details"
                }
            ]
        }
        """
        data, metadata = self.parser.parse_response(response, ResponseType.TYPE_SPECIFIC)
        self.assertTrue(data["satisfied"])
        self.assertEqual(data["completeness_score"], 0.95)
    
    def test_json_extraction_from_text(self):
        """Test extracting JSON from text with surrounding content"""
        response = """
        Here is the analysis:
        ```json
        {
            "satisfied": true,
            "explanation": "test",
            "found_keywords": [],
            "missing_keywords": [],
            "confidence_score": 1.0
        }
        ```
        End of analysis.
        """
        data, metadata = self.parser.parse_response(response, ResponseType.COMPLETENESS_CHECK)
        self.assertTrue(data["satisfied"])
        self.assertEqual(metadata.extraction_method, "regex")
    
    def test_invalid_json(self):
        """Test handling of invalid JSON"""
        response = "{ invalid json }"
        with self.assertRaises(ValueError):
            self.parser.parse_response(response, ResponseType.COMPLETENESS_CHECK)
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        response = """
        {
            "satisfied": true,
            "explanation": "test"
        }
        """
        with self.assertRaises(Exception):
            self.parser.parse_response(response, ResponseType.COMPLETENESS_CHECK)
    
    def test_empty_response(self):
        """Test handling of empty response"""
        response = ""
        with self.assertRaises(ValueError):
            self.parser.parse_response(response, ResponseType.COMPLETENESS_CHECK)
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        response = """
        {
            "satisfied": true,
            "explanation": "test",
            "found_keywords": [],
            "missing_keywords": [],
            "confidence_score": 0.8,
            "suggestions": []
        }
        """
        data, metadata = self.parser.parse_response(response, ResponseType.COMPLETENESS_CHECK)
        self.assertLessEqual(metadata.confidence_score, 0.8)
    
    def test_large_response(self):
        """Test handling of large response"""
        # Create a large response with repeated content
        base_content = {
            "satisfied": True,
            "explanation": "test" * 100,  # Long explanation
            "found_keywords": ["word" + str(i) for i in range(100)],
            "missing_keywords": [],
            "confidence_score": 0.9
        }
        response = json.dumps(base_content)
        data, metadata = self.parser.parse_response(response, ResponseType.COMPLETENESS_CHECK)
        self.assertEqual(len(data["found_keywords"]), 100)
    
    def test_format_output(self):
        """Test output formatting"""
        response = """
        {
            "satisfied": true,
            "explanation": "test",
            "found_keywords": [],
            "missing_keywords": [],
            "confidence_score": 1.0
        }
        """
        data, metadata = self.parser.parse_response(response, ResponseType.COMPLETENESS_CHECK)
        formatted = self.parser.format_output(data, metadata)
        
        self.assertIn("data", formatted)
        self.assertIn("metadata", formatted)
        self.assertEqual(formatted["metadata"]["response_type"], "completeness_check")

def run_tests():
    """Run all tests and return results"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLLMResponseParser)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == "__main__":
    run_tests() 