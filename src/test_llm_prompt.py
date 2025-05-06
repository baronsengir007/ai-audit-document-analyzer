"""
Test suite for policy document requirement extraction with LLM integration.
Tests prompt effectiveness, response parsing, error handling, and performance.
"""

import os
import time
import unittest
import json
import logging
from pathlib import Path
from typing import List

from policy_parser import PolicyParser, ComplianceRequirement, RequirementType
from llm_wrapper import OllamaWrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("test_policy_parser")

class TestPolicyRequirementExtraction(unittest.TestCase):
    """Test suite for policy requirement extraction functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Initialize the LLM wrapper
        cls.llm = OllamaWrapper(model="mistral")
        
        # Initialize the policy parser
        cls.parser = PolicyParser(llm=cls.llm)
        
        # Define test policy documents
        cls.test_docs_dir = Path("docs")
        cls.sample_policy_txt = cls.test_docs_dir / "sample_policy.txt"
        
        # Create output directory if it doesn't exist
        cls.output_dir = Path("outputs")
        os.makedirs(cls.output_dir, exist_ok=True)
    
    def test_chunk_text(self):
        """Test the semantic text chunking functionality"""
        # Load sample policy document
        with open(self.sample_policy_txt, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Test chunking
        chunks = self.parser._chunk_text(text)
        
        # Verify that chunks are created and have section information
        self.assertTrue(len(chunks) > 0, "No chunks were created")
        
        # Check that chunks contain tuples of (text, section_info)
        for chunk in chunks:
            self.assertTrue(isinstance(chunk, tuple), "Chunk is not a tuple")
            self.assertEqual(len(chunk), 2, "Chunk tuple does not have 2 elements")
            chunk_text, section_info = chunk
            self.assertTrue(isinstance(chunk_text, str), "Chunk text is not a string")
            self.assertTrue(isinstance(section_info, str), "Section info is not a string")
        
        logger.info(f"Text chunking created {len(chunks)} chunks")
    
    def test_extract_requirements_from_chunk(self):
        """Test extraction of requirements from a single text chunk"""
        # Use a small, well-defined chunk for testing
        test_chunk = """
        Section 1: Password Requirements
        
        1.1 All users must use strong passwords with at least 12 characters.
        1.2 Passwords must contain uppercase letters, lowercase letters, numbers, and special characters.
        1.3 Users should change their passwords every 90 days.
        1.4 Sharing of passwords is prohibited.
        """
        
        section_info = "Section 1: Password Requirements"
        
        # Extract requirements
        start_time = time.time()
        requirements = self.parser._extract_requirements_from_chunk(test_chunk, section_info)
        elapsed_time = time.time() - start_time
        
        # Verify requirements were extracted
        self.assertTrue(len(requirements) > 0, "No requirements extracted")
        
        # Check extracted requirements structure
        for req in requirements:
            self.assertIn("id", req, "Requirement missing id field")
            self.assertIn("description", req, "Requirement missing description field")
            self.assertIn("type", req, "Requirement missing type field")
            self.assertIn("priority", req, "Requirement missing priority field")
            
            # Verify types are correct
            self.assertIn(req["type"], ["mandatory", "recommended", "prohibited"], 
                         f"Invalid requirement type: {req['type']}")
        
        logger.info(f"Extracted {len(requirements)} requirements in {elapsed_time:.2f} seconds")
        logger.info(f"Sample requirement: {requirements[0]}")
    
    def test_parse_policy_document(self):
        """Test full policy document parsing functionality"""
        # Test with sample policy document
        if not self.sample_policy_txt.exists():
            self.skipTest(f"Sample policy file not found: {self.sample_policy_txt}")
        
        # Parse document and measure performance
        start_time = time.time()
        requirements = self.parser.parse_policy_document(self.sample_policy_txt)
        elapsed_time = time.time() - start_time
        
        # Verify requirements were extracted
        self.assertTrue(len(requirements) > 0, "No requirements extracted from policy document")
        
        # Check all requirements are valid ComplianceRequirement objects
        for req in requirements:
            self.assertIsInstance(req, ComplianceRequirement, "Result is not a ComplianceRequirement object")
            
            # Check mandatory fields are present
            self.assertTrue(req.id, "Requirement has empty id")
            self.assertTrue(req.description, "Requirement has empty description")
            
            # Verify requirement type is one of the valid enum values
            self.assertIn(req.type, RequirementType, "Invalid requirement type")
        
        # Performance check
        self.assertLess(elapsed_time, 120, "Policy parsing took too long (>120 seconds)")
        
        # Log performance metrics
        logger.info(f"Parsed policy document in {elapsed_time:.2f} seconds")
        logger.info(f"Extracted {len(requirements)} requirements")
        
        # Calculate requirement type distribution
        type_counts = {}
        for req in requirements:
            req_type = req.type.value
            type_counts[req_type] = type_counts.get(req_type, 0) + 1
        
        logger.info(f"Requirement types: {type_counts}")
        
        # Save requirements to output file for manual inspection
        output_path = self.output_dir / "test_requirements.json"
        self.parser.save_requirements(requirements, output_path)
        logger.info(f"Requirements saved to {output_path}")
    
    def test_relationship_identification(self):
        """Test identification of relationships between requirements"""
        # Create test requirements
        test_requirements = [
            ComplianceRequirement(
                id="req_1",
                description="Passwords must be at least 12 characters long",
                type=RequirementType.MANDATORY,
                priority=RequirementType.HIGH,
                source=RequirementType("Password Policy"),
                confidence_score=0.9,
                category="Authentication"
            ),
            ComplianceRequirement(
                id="req_2",
                description="Password change must be enforced every 90 days",
                type=RequirementType.MANDATORY,
                priority=RequirementType.MEDIUM,
                source=RequirementType("Password Policy"),
                confidence_score=0.9,
                category="Authentication"
            )
        ]
        
        # Test relationship identification
        self.parser._identify_relationships(test_requirements)
        
        # Relationships may or may not be found, but the function should run without errors
        logger.info(f"Relationship identification completed")
        
        # Log any identified relationships
        for req in test_requirements:
            if req.relationships:
                logger.info(f"Requirement {req.id} has {len(req.relationships)} relationships")
    
    def test_error_handling(self):
        """Test error handling in policy parser"""
        # Test with invalid file path
        invalid_path = Path("nonexistent_file.txt")
        with self.assertRaises(Exception):
            self.parser.parse_policy_document(invalid_path)
        
        # Test with unsupported file type
        unsupported_path = Path("test.xyz")
        
        # Create empty file with unsupported extension
        with open(unsupported_path, 'w') as f:
            f.write("Test content")
        
        try:
            with self.assertRaises(ValueError):
                self.parser.parse_policy_document(unsupported_path)
        finally:
            # Clean up test file
            if unsupported_path.exists():
                os.remove(unsupported_path)

# Execute tests if run directly
if __name__ == "__main__":
    unittest.main()