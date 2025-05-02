"""
Test suite for the policy parser module.
"""

import unittest
import json
import logging
from pathlib import Path
import tempfile
from datetime import datetime
from typing import Dict, List

from policy_parser import (
    PolicyParser,
    RequirementType,
    RequirementPriority,
    ComplianceRequirement,
    RequirementSource,
    RequirementRelationship
)

class TestPolicyParser(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.parser = PolicyParser()
        logging.basicConfig(level=logging.INFO)
        
        # Create sample policy documents
        self.sample_policy = """
        Security Policy Document
        
        Section 1: Access Control
        1.1 All users must use strong passwords (minimum 12 characters).
        1.2 Multi-factor authentication is recommended for all systems.
        1.3 Users are prohibited from sharing their credentials.
        
        Section 2: Data Protection
        2.1 All sensitive data must be encrypted at rest.
        2.2 Regular backups are recommended for all critical systems.
        2.3 Unauthorized data access is strictly prohibited.
        """
        
        self.sample_policy_path = self.test_dir / "sample_policy.txt"
        with open(self.sample_policy_path, "w", encoding="utf-8") as f:
            f.write(self.sample_policy)
        
        # Create sample requirements for testing
        self.sample_requirements = [
            ComplianceRequirement(
                id="req1",
                description="All users must use strong passwords",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.HIGH,
                category="Access Control",
                source=RequirementSource(
                    document_section="Section 1",
                    context="All users must use strong passwords (minimum 12 characters)."
                ),
                confidence_score=0.95,
                keywords=["password", "security"]
            ),
            ComplianceRequirement(
                id="req2",
                description="Multi-factor authentication is recommended",
                type=RequirementType.RECOMMENDED,
                priority=RequirementPriority.MEDIUM,
                category="Access Control",
                source=RequirementSource(
                    document_section="Section 1",
                    context="Multi-factor authentication is recommended for all systems."
                ),
                confidence_score=0.9,
                keywords=["authentication", "security"]
            )
        ]
    
    def test_requirement_type_enum(self):
        """Test RequirementType enum values"""
        self.assertEqual(RequirementType.MANDATORY.value, "mandatory")
        self.assertEqual(RequirementType.RECOMMENDED.value, "recommended")
        self.assertEqual(RequirementType.PROHIBITED.value, "prohibited")
    
    def test_requirement_priority_enum(self):
        """Test RequirementPriority enum values"""
        self.assertEqual(RequirementPriority.CRITICAL.value, "critical")
        self.assertEqual(RequirementPriority.HIGH.value, "high")
        self.assertEqual(RequirementPriority.MEDIUM.value, "medium")
        self.assertEqual(RequirementPriority.LOW.value, "low")
    
    def test_text_preprocessing(self):
        """Test text preprocessing functionality"""
        input_text = "  This is a test.\n\nWith multiple  spaces  and\nline breaks.  "
        expected = "This is a test. With multiple spaces and line breaks."
        processed = self.parser._preprocess_text(input_text)
        self.assertEqual(processed, expected)
    
    def test_text_chunking(self):
        """Test text chunking functionality"""
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        chunks = self.parser._chunk_text(text, chunk_size=20)
        self.assertEqual(len(chunks), 3)
        self.assertTrue(all(len(chunk) <= 20 for chunk in chunks))
    
    def test_requirement_extraction(self):
        """Test requirement extraction from text chunk"""
        chunk = """
        Section 1: Access Control
        1.1 All users must use strong passwords (minimum 12 characters).
        1.2 Multi-factor authentication is recommended for all systems.
        """
        
        requirements = self.parser._extract_requirements_from_chunk(chunk)
        self.assertGreater(len(requirements), 0)
        
        # Check structure of extracted requirements
        for req in requirements:
            self.assertIn("id", req)
            self.assertIn("description", req)
            self.assertIn("type", req)
            self.assertIn("priority", req)
            self.assertIn("category", req)
            self.assertIn("source", req)
    
    def test_requirement_merging(self):
        """Test requirement merging and deduplication"""
        raw_requirements = [
            {
                "id": "req1",
                "description": "Test requirement 1",
                "type": "mandatory",
                "priority": "high",
                "category": "Test",
                "source": {"document_section": "Section 1"}
            },
            {
                "id": "req1",  # Duplicate ID
                "description": "Test requirement 1",
                "type": "mandatory",
                "priority": "high",
                "category": "Test",
                "source": {"document_section": "Section 1"}
            },
            {
                "id": "req2",
                "description": "Test requirement 2",
                "type": "recommended",
                "priority": "medium",
                "category": "Test",
                "source": {"document_section": "Section 1"}
            }
        ]
        
        merged = self.parser._merge_requirements(raw_requirements)
        self.assertEqual(len(merged), 2)  # Should have 2 unique requirements
    
    def test_relationship_identification(self):
        """Test relationship identification between requirements"""
        requirements = self.sample_requirements
        self.parser._identify_relationships(requirements)
        
        # Check if relationships were added
        has_relationships = any(len(req.relationships) > 0 for req in requirements)
        self.assertTrue(has_relationships)
    
    def test_policy_document_parsing(self):
        """Test full policy document parsing"""
        requirements = self.parser.parse_policy_document(self.sample_policy_path)
        self.assertGreater(len(requirements), 0)
        
        # Check requirement types
        requirement_types = {req.type for req in requirements}
        self.assertTrue(RequirementType.MANDATORY in requirement_types)
        self.assertTrue(RequirementType.RECOMMENDED in requirement_types)
        self.assertTrue(RequirementType.PROHIBITED in requirement_types)
    
    def test_requirement_saving(self):
        """Test saving requirements to file"""
        output_path = self.test_dir / "requirements.json"
        self.parser.save_requirements(self.sample_requirements, output_path)
        
        # Verify file exists and is valid JSON
        self.assertTrue(output_path.exists())
        with open(output_path) as f:
            data = json.load(f)
            self.assertIn("requirements", data)
            self.assertIn("metadata", data)
            self.assertEqual(len(data["requirements"]), len(self.sample_requirements))
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test with non-existent file
        with self.assertRaises(Exception):
            self.parser.parse_policy_document(Path("nonexistent.txt"))
        
        # Test with unsupported file type
        invalid_file = self.test_dir / "test.invalid"
        invalid_file.touch()
        with self.assertRaises(ValueError):
            self.parser.parse_policy_document(invalid_file)
    
    def test_confidence_scores(self):
        """Test confidence score assignment"""
        requirements = self.parser.parse_policy_document(self.sample_policy_path)
        for req in requirements:
            self.assertGreaterEqual(req.confidence_score, 0.0)
            self.assertLessEqual(req.confidence_score, 1.0)
    
    def test_requirement_categorization(self):
        """Test requirement categorization"""
        requirements = self.parser.parse_policy_document(self.sample_policy_path)
        categories = {req.category for req in requirements}
        self.assertTrue("Access Control" in categories)
        self.assertTrue("Data Protection" in categories)
    
    def test_requirement_metadata(self):
        """Test requirement metadata handling"""
        requirements = self.parser.parse_policy_document(self.sample_policy_path)
        for req in requirements:
            self.assertIsInstance(req.metadata, dict)
            self.assertIsInstance(req.keywords, list)

if __name__ == "__main__":
    unittest.main() 