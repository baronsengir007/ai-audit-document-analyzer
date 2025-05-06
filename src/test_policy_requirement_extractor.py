import unittest
import json
import sys
import os
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.policy_requirement_extractor import PolicyRequirementExtractor
from src.llm_wrapper import OllamaWrapper

class TestPolicyRequirementExtractor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm = MagicMock(spec=OllamaWrapper)
        self.extractor = PolicyRequirementExtractor(self.mock_llm)
        
        # Sample policy document
        self.sample_doc = {
            "filename": "test_policy.pdf",
            "type": "policy",
            "content": """
            Security Policy Document
            
            Section 1: Access Control
            All employees must use strong passwords for their accounts.
            Passwords shall be changed every 90 days.
            Multi-factor authentication is required for remote access.
            
            Section 2: Data Protection
            Sensitive data must be encrypted at rest.
            Regular backups are mandatory.
            Data retention policies shall be followed.
            """
        }
        
        # Sample LLM response
        self.sample_response = {
            "response": json.dumps([
                {
                    "id": "req_1",
                    "requirement_text": "All employees must use strong passwords for their accounts",
                    "type": "explicit",
                    "keywords": ["strong", "passwords"],
                    "conditions": [],
                    "confidence": 0.95
                },
                {
                    "id": "req_2",
                    "requirement_text": "Passwords shall be changed every 90 days",
                    "type": "explicit",
                    "keywords": ["passwords", "changed", "90 days"],
                    "conditions": [],
                    "confidence": 0.9
                }
            ])
        }
    
    def test_chunk_document(self):
        """Test document chunking functionality."""
        # Test with small document
        small_doc = "Short document"
        chunks = self.extractor._chunk_document(small_doc)
        print(f"\nSmall doc test - Chunks: {chunks}")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], small_doc)
        
        # Test with document larger than chunk size
        large_doc = "Paragraph 1\n\n" * 1000
        chunks = self.extractor._chunk_document(large_doc)
        print(f"\nLarge doc test - Number of chunks: {len(chunks)}")
        print(f"First chunk length: {len(chunks[0])}")
        print(f"Chunk size limit: {self.extractor.chunk_size}")
        self.assertGreater(len(chunks), 1)
        
        # Test chunk size limits
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i} size: {len(chunk)}")
            self.assertLessEqual(len(chunk), self.extractor.chunk_size)
    
    def test_extract_requirements_from_chunk(self):
        """Test requirement extraction from a single chunk."""
        # Mock LLM response
        self.mock_llm._make_request.return_value = self.sample_response
        
        # Test extraction
        requirements = self.extractor._extract_requirements_from_chunk(
            "Sample chunk",
            {"filename": "test.pdf", "type": "policy"}
        )
        
        # Verify results
        self.assertEqual(len(requirements), 2)
        self.assertEqual(requirements[0]["type"], "explicit")
        self.assertIn("passwords", requirements[0]["keywords"])
    
    def test_extract_requirements(self):
        """Test full requirement extraction process."""
        # Mock LLM response
        self.mock_llm._make_request.return_value = self.sample_response
        
        # Test extraction
        requirements = self.extractor.extract_requirements(self.sample_doc)
        
        # Verify results
        self.assertGreater(len(requirements), 0)
        self.assertTrue(all("id" in req for req in requirements))
        self.assertTrue(all("requirement_text" in req for req in requirements))
        self.assertTrue(all("type" in req for req in requirements))
    
    def test_validate_requirements(self):
        """Test requirement validation."""
        # Create test requirements
        test_requirements = [
            {
                "id": "req_1",
                "requirement_text": "Test requirement 1",
                "type": "explicit",
                "keywords": ["test"],
                "conditions": [],
                "confidence": 0.9
            },
            {
                "id": "req_2",
                "requirement_text": "Test requirement 2",
                "type": "implicit",
                "keywords": [],
                "conditions": [],
                "confidence": 0.3
            }
        ]
        
        # Test validation
        validation = self.extractor.validate_requirements(test_requirements)
        
        # Verify results
        self.assertEqual(validation["total_requirements"], 2)
        self.assertEqual(validation["explicit_requirements"], 1)
        self.assertEqual(validation["implicit_requirements"], 1)
        self.assertLess(validation["average_confidence"], 0.7)
        self.assertEqual(len(validation["issues"]), 2)  # One for missing keywords, one for low confidence
    
    def test_error_handling(self):
        """Test error handling in requirement extraction."""
        # Mock LLM to raise an exception
        self.mock_llm._make_request.side_effect = Exception("Test error")
        
        # Test extraction with error
        requirements = self.extractor._extract_requirements_from_chunk(
            "Sample chunk",
            {"filename": "test.pdf", "type": "policy"}
        )
        
        # Verify empty result on error
        self.assertEqual(requirements, [])
    
    def test_duplicate_requirement_handling(self):
        """Test handling of duplicate requirements."""
        # Mock LLM to return duplicate requirements
        duplicate_response = {
            "response": json.dumps([
                {
                    "id": "req_1",
                    "requirement_text": "Same requirement",
                    "type": "explicit",
                    "keywords": ["test"],
                    "conditions": [],
                    "confidence": 0.9
                },
                {
                    "id": "req_2",
                    "requirement_text": "Same requirement",
                    "type": "explicit",
                    "keywords": ["test"],
                    "conditions": [],
                    "confidence": 0.9
                }
            ])
        }
        self.mock_llm._make_request.return_value = duplicate_response
        
        # Test extraction
        requirements = self.extractor.extract_requirements(self.sample_doc)
        
        # Verify duplicates are removed
        self.assertEqual(len(requirements), 1)

if __name__ == "__main__":
    unittest.main() 