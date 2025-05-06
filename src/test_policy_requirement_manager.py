"""
Test suite for PolicyRequirementManager integration
Verifies integration between policy parser and requirement store
"""

import unittest
import tempfile
import os
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

from policy_requirement_manager import PolicyRequirementManager
from policy_parser import (
    PolicyParser,
    ComplianceRequirement,
    RequirementType,
    RequirementPriority,
    RequirementSource
)
from requirement_store import RequirementStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("test_policy_requirement_manager")

class TestPolicyRequirementManager(unittest.TestCase):
    """Test PolicyRequirementManager integration functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for YAML files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.yaml_path = Path(self.temp_dir.name) / "test_requirements.yaml"
        
        # Create mock parser
        self.mock_parser = MagicMock(spec=PolicyParser)
        
        # Create manager with mock parser and real store
        self.manager = PolicyRequirementManager(
            yaml_path=self.yaml_path,
            parser=self.mock_parser,
            store=RequirementStore(yaml_path=self.yaml_path)
        )
        
        # Create sample requirements for testing
        self.sample_requirements = [
            ComplianceRequirement(
                id="req_001",
                description="All passwords must be at least 12 characters long",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.HIGH,
                source=RequirementSource(document_section="Section 1: Access Control"),
                confidence_score=0.95,
                category="Authentication",
                subcategory="Password Policy",
                keywords=["password", "length", "security"],
                metadata={}
            ),
            ComplianceRequirement(
                id="req_002",
                description="System logs must be retained for at least 6 months",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.MEDIUM,
                source=RequirementSource(document_section="Section 3: Logging"),
                confidence_score=0.9,
                category="Logging",
                subcategory="Retention",
                keywords=["logs", "retention", "audit"],
                metadata={}
            )
        ]
    
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    def test_extract_and_store(self):
        """Test extract_and_store method for end-to-end workflow"""
        # Configure mock parser to return sample requirements
        self.mock_parser.parse_policy_document.return_value = self.sample_requirements
        
        # Test extraction and storage
        file_path = Path("test_policy.txt")
        result = self.manager.extract_and_store(file_path)
        
        # Verify parser was called
        self.mock_parser.parse_policy_document.assert_called_once_with(file_path)
        
        # Verify requirements were stored
        self.assertEqual(len(result), 2, "Expected 2 results")
        self.assertTrue(all(result.values()), "Expected all additions to succeed")
        
        # Verify requirements can be retrieved
        requirements = self.manager.get_all_requirements()
        self.assertEqual(len(requirements), 2, "Expected 2 requirements stored")
        
        # Verify metadata was added
        for req in requirements:
            self.assertIn("source_file", req.metadata, "Missing source_file metadata")
            self.assertIn("extraction_date", req.metadata, "Missing extraction_date metadata")
    
    def test_get_requirements_filtering(self):
        """Test getting requirements with filtering"""
        # Add sample requirements directly to store
        self.manager.store.add_requirements(self.sample_requirements)
        
        # Test filtering by category
        auth_reqs = self.manager.get_requirements(category="Authentication")
        self.assertEqual(len(auth_reqs), 1, "Expected 1 Authentication requirement")
        self.assertEqual(auth_reqs[0].id, "req_001")
        
        # Test filtering by type
        mandatory_reqs = self.manager.get_requirements(req_type="mandatory")
        self.assertEqual(len(mandatory_reqs), 2, "Expected 2 mandatory requirements")
        
        # Test filtering by priority
        high_reqs = self.manager.get_requirements(priority="high")
        self.assertEqual(len(high_reqs), 1, "Expected 1 high priority requirement")
    
    def test_get_requirement_by_id(self):
        """Test getting a requirement by ID"""
        # Add sample requirements directly to store
        self.manager.store.add_requirements(self.sample_requirements)
        
        # Test getting by ID
        req = self.manager.get_requirement("req_001")
        self.assertIsNotNone(req, "Failed to get requirement by ID")
        self.assertEqual(req.id, "req_001")
        self.assertEqual(req.description, self.sample_requirements[0].description)
    
    def test_yaml_persistence(self):
        """Test YAML persistence through the manager"""
        # Add sample requirements directly to store
        self.manager.store.add_requirements(self.sample_requirements)
        
        # Save to YAML
        self.manager.save_to_yaml()
        
        # Verify file was created
        self.assertTrue(self.yaml_path.exists(), "YAML file was not created")
        
        # Create a new manager with the same path
        new_manager = PolicyRequirementManager(yaml_path=self.yaml_path)
        
        # Verify requirements were loaded
        loaded_reqs = new_manager.get_all_requirements()
        self.assertEqual(len(loaded_reqs), 2, "Expected 2 requirements after loading")
        
        # Verify stats
        stats = new_manager.get_stats()
        self.assertEqual(stats["total_requirements"], 2, "Expected 2 total requirements")
        self.assertEqual(stats["by_category"]["Authentication"], 1, "Expected 1 Authentication requirement")
        self.assertEqual(stats["by_category"]["Logging"], 1, "Expected 1 Logging requirement")
    
    def test_export_to_json(self):
        """Test exporting requirements to JSON"""
        # Add sample requirements directly to store
        self.manager.store.add_requirements(self.sample_requirements)
        
        # Create JSON export path
        json_path = Path(self.temp_dir.name) / "requirements.json"
        
        # Export to JSON
        self.manager.export_to_json(json_path)
        
        # Verify file was created
        self.assertTrue(json_path.exists(), "JSON file was not created")
    
    def test_error_handling(self):
        """Test error handling in extract_and_store"""
        # Configure mock parser to raise an exception
        self.mock_parser.parse_policy_document.side_effect = ValueError("Test error")
        
        # Test extraction and storage with error
        with self.assertRaises(ValueError):
            self.manager.extract_and_store(Path("test_policy.txt"))
    
    @patch('policy_requirement_manager.PolicyParser')
    @patch('policy_requirement_manager.RequirementStore')
    def test_integration_interfaces(self, mock_store_class, mock_parser_class):
        """Test that manager correctly integrates with parser and store interfaces"""
        # Create mock instances
        mock_parser = mock_parser_class.return_value
        mock_store = mock_store_class.return_value
        
        # Configure mock parser to return sample requirements
        mock_parser.parse_policy_document.return_value = self.sample_requirements
        
        # Create manager with mocks
        manager = PolicyRequirementManager(
            parser=mock_parser,
            store=mock_store
        )
        
        # Test extract_and_store
        file_path = Path("test_policy.txt")
        manager.extract_and_store(file_path)
        
        # Verify parser was called
        mock_parser.parse_policy_document.assert_called_once_with(file_path)
        
        # Verify store was called with the requirements
        mock_store.add_requirements.assert_called_once()
        args, _ = mock_store.add_requirements.call_args
        self.assertEqual(len(args[0]), 2, "Expected 2 requirements added to store")
        
        # Verify other manager methods call corresponding store methods
        manager.get_all_requirements()
        mock_store.get_all_requirements.assert_called_once()
        
        manager.get_requirements(category="test")
        mock_store.filter_requirements.assert_called_once_with(category="test")
        
        # Verify save_to_yaml was called (may be called multiple times due to auto_save)
        self.assertTrue(mock_store.save_to_yaml.called, "save_to_yaml should have been called")

# Main function
if __name__ == "__main__":
    unittest.main()