"""
Test suite for RequirementStore functionality
Verifies in-memory storage, YAML persistence, validation, and queries.
"""

import unittest
import tempfile
import os
import logging
from pathlib import Path
from datetime import datetime
import yaml

from requirement_store import RequirementStore, RequirementValidator, RequirementSerializer
from policy_parser import (
    ComplianceRequirement,
    RequirementType,
    RequirementPriority,
    RequirementSource,
    RequirementRelationship
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("test_requirement_store")

class TestRequirementValidator(unittest.TestCase):
    """Test requirement validation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.validator = RequirementValidator()
        
        # Create a valid requirement for testing
        self.valid_requirement = ComplianceRequirement(
            id="req_001",
            description="All passwords must be at least 12 characters long",
            type=RequirementType.MANDATORY,
            priority=RequirementPriority.HIGH,
            source=RequirementSource(document_section="Section 1: Access Control"),
            confidence_score=0.95,
            category="Authentication",
            subcategory="Password Policy",
            keywords=["password", "length", "security"]
        )
    
    def test_valid_requirement(self):
        """Test validation of a valid requirement"""
        errors = self.validator.validate_requirement(self.valid_requirement)
        self.assertEqual(len(errors), 0, "Expected no validation errors for valid requirement")
    
    def test_missing_id(self):
        """Test validation with missing ID"""
        invalid_req = ComplianceRequirement(
            id="",  # Empty ID
            description="Test description",
            type=RequirementType.MANDATORY,
            priority=RequirementPriority.MEDIUM,
            source=RequirementSource(document_section="Test"),
            confidence_score=0.5,
            category="Test"
        )
        
        errors = self.validator.validate_requirement(invalid_req)
        self.assertTrue(any("ID is required" in err for err in errors), 
                      "Expected validation error for missing ID")
    
    def test_invalid_type(self):
        """Test validation with invalid type"""
        # Create a copy of the valid requirement
        invalid_req = ComplianceRequirement(
            id=self.valid_requirement.id,
            description=self.valid_requirement.description,
            type="invalid_type",  # Invalid type
            priority=self.valid_requirement.priority,
            source=self.valid_requirement.source,
            confidence_score=self.valid_requirement.confidence_score,
            category=self.valid_requirement.category
        )
        
        errors = self.validator.validate_requirement(invalid_req)
        self.assertTrue(any("type" in err.lower() for err in errors), 
                      "Expected validation error for invalid type")
    
    def test_invalid_confidence_score(self):
        """Test validation with invalid confidence score"""
        # Create a copy of the valid requirement with invalid confidence score
        invalid_req = ComplianceRequirement(
            id=self.valid_requirement.id,
            description=self.valid_requirement.description,
            type=self.valid_requirement.type,
            priority=self.valid_requirement.priority,
            source=self.valid_requirement.source,
            confidence_score=2.0,  # Invalid score (> 1.0)
            category=self.valid_requirement.category
        )
        
        errors = self.validator.validate_requirement(invalid_req)
        self.assertTrue(any("confidence score" in err.lower() for err in errors), 
                      "Expected validation error for invalid confidence score")

class TestRequirementSerializer(unittest.TestCase):
    """Test requirement serialization functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.serializer = RequirementSerializer()
        
        # Create a sample requirement with relationships
        source = RequirementSource(
            document_section="Section 1: Access Control",
            context="Context information"
        )
        
        relationship = RequirementRelationship(
            target_id="req_002",
            relationship_type="depends_on",
            description="Dependency relationship"
        )
        
        self.requirement = ComplianceRequirement(
            id="req_001",
            description="All passwords must be at least 12 characters long",
            type=RequirementType.MANDATORY,
            priority=RequirementPriority.HIGH,
            source=source,
            confidence_score=0.95,
            category="Authentication",
            subcategory="Password Policy",
            relationships=[relationship],
            keywords=["password", "length", "security"],
            metadata={"created_date": "2024-01-01"}
        )
    
    def test_serialization_to_dict(self):
        """Test serialization of requirement to dictionary"""
        result = self.serializer.to_serializable(self.requirement)
        
        # Check that the result is a dictionary
        self.assertIsInstance(result, dict)
        
        # Check that all expected fields are present
        self.assertEqual(result["id"], self.requirement.id)
        self.assertEqual(result["description"], self.requirement.description)
        self.assertEqual(result["type"], self.requirement.type.value)
        self.assertEqual(result["priority"], self.requirement.priority.value)
        self.assertEqual(result["category"], self.requirement.category)
        self.assertEqual(result["subcategory"], self.requirement.subcategory)
        self.assertEqual(result["keywords"], self.requirement.keywords)
        self.assertEqual(result["confidence_score"], self.requirement.confidence_score)
        
        # Check nested objects
        self.assertIsInstance(result["source"], dict)
        self.assertEqual(result["source"]["document_section"], 
                       self.requirement.source.document_section)
        
        # Check relationships
        self.assertIsInstance(result["relationships"], list)
        self.assertEqual(len(result["relationships"]), 1)
        self.assertEqual(result["relationships"][0]["target_id"], 
                       self.requirement.relationships[0].target_id)
    
    def test_deserialization_from_dict(self):
        """Test deserialization of dictionary to requirement"""
        # First serialize the requirement
        serialized = self.serializer.to_serializable(self.requirement)
        
        # Then deserialize it
        deserialized = self.serializer.from_dict(serialized)
        
        # Check that the result is a ComplianceRequirement
        self.assertIsInstance(deserialized, ComplianceRequirement)
        
        # Check that all expected fields match
        self.assertEqual(deserialized.id, self.requirement.id)
        self.assertEqual(deserialized.description, self.requirement.description)
        self.assertEqual(deserialized.type, self.requirement.type)
        self.assertEqual(deserialized.priority, self.requirement.priority)
        self.assertEqual(deserialized.category, self.requirement.category)
        self.assertEqual(deserialized.subcategory, self.requirement.subcategory)
        self.assertEqual(deserialized.keywords, self.requirement.keywords)
        self.assertEqual(deserialized.confidence_score, self.requirement.confidence_score)
        
        # Check nested objects
        self.assertEqual(deserialized.source.document_section, 
                       self.requirement.source.document_section)
        
        # Check relationships
        self.assertEqual(len(deserialized.relationships), 1)
        self.assertEqual(deserialized.relationships[0].target_id, 
                       self.requirement.relationships[0].target_id)

class TestRequirementStore(unittest.TestCase):
    """Test requirement store functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for YAML files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.yaml_path = Path(self.temp_dir.name) / "test_requirements.yaml"
        
        # Create the store with the test path
        self.store = RequirementStore(yaml_path=self.yaml_path)
        
        # Create sample requirements for testing
        self.req1 = ComplianceRequirement(
            id="req_001",
            description="All passwords must be at least 12 characters long",
            type=RequirementType.MANDATORY,
            priority=RequirementPriority.HIGH,
            source=RequirementSource(document_section="Section 1: Access Control"),
            confidence_score=0.95,
            category="Authentication",
            subcategory="Password Policy",
            keywords=["password", "length", "security"]
        )
        
        self.req2 = ComplianceRequirement(
            id="req_002",
            description="System logs must be retained for at least 6 months",
            type=RequirementType.MANDATORY,
            priority=RequirementPriority.MEDIUM,
            source=RequirementSource(document_section="Section 3: Logging"),
            confidence_score=0.9,
            category="Logging",
            subcategory="Retention",
            keywords=["logs", "retention", "audit"]
        )
        
        self.req3 = ComplianceRequirement(
            id="req_003",
            description="Users should change passwords every 90 days",
            type=RequirementType.RECOMMENDED,
            priority=RequirementPriority.MEDIUM,
            source=RequirementSource(document_section="Section 1: Access Control"),
            confidence_score=0.8,
            category="Authentication",
            subcategory="Password Policy",
            keywords=["password", "rotation", "expiry"]
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    def test_add_requirement(self):
        """Test adding a requirement to the store"""
        # Add a requirement
        result = self.store.add_requirement(self.req1)
        
        # Check the result
        self.assertTrue(result, "Failed to add valid requirement")
        
        # Check that the requirement was added
        requirements = self.store.get_all_requirements()
        self.assertEqual(len(requirements), 1, "Expected 1 requirement in store")
        self.assertEqual(requirements[0].id, self.req1.id)
    
    def test_add_duplicate(self):
        """Test adding a duplicate requirement"""
        # Add a requirement
        self.store.add_requirement(self.req1)
        
        # Try to add it again
        result = self.store.add_requirement(self.req1)
        
        # Check the result
        self.assertFalse(result, "Should not be able to add duplicate requirement")
        
        # Check that only one requirement is in the store
        requirements = self.store.get_all_requirements()
        self.assertEqual(len(requirements), 1, "Expected 1 requirement in store")
    
    def test_update_requirement(self):
        """Test updating a requirement"""
        # Add a requirement
        self.store.add_requirement(self.req1)
        
        # Create an updated version
        updated_req = ComplianceRequirement(
            id=self.req1.id,
            description="Updated description",
            type=self.req1.type,
            priority=self.req1.priority,
            source=self.req1.source,
            confidence_score=self.req1.confidence_score,
            category=self.req1.category
        )
        
        # Update the requirement
        result = self.store.update_requirement(updated_req)
        
        # Check the result
        self.assertTrue(result, "Failed to update requirement")
        
        # Check that the requirement was updated
        requirement = self.store.get_requirement(self.req1.id)
        self.assertEqual(requirement.description, "Updated description")
    
    def test_get_requirement(self):
        """Test getting a requirement by ID"""
        # Add a requirement
        self.store.add_requirement(self.req1)
        
        # Get the requirement
        requirement = self.store.get_requirement(self.req1.id)
        
        # Check that we got the correct requirement
        self.assertIsNotNone(requirement, "Failed to get requirement")
        self.assertEqual(requirement.id, self.req1.id)
        self.assertEqual(requirement.description, self.req1.description)
    
    def test_get_nonexistent_requirement(self):
        """Test getting a requirement that doesn't exist"""
        # Get a nonexistent requirement
        requirement = self.store.get_requirement("nonexistent")
        
        # Check that we got None
        self.assertIsNone(requirement, "Expected None for nonexistent requirement")
    
    def test_filter_requirements(self):
        """Test filtering requirements"""
        # Add multiple requirements
        self.store.add_requirement(self.req1)
        self.store.add_requirement(self.req2)
        self.store.add_requirement(self.req3)
        
        # Filter by category
        auth_reqs = self.store.filter_requirements(category="Authentication")
        self.assertEqual(len(auth_reqs), 2, "Expected 2 Authentication requirements")
        
        # Filter by type
        mandatory_reqs = self.store.filter_requirements(req_type=RequirementType.MANDATORY)
        self.assertEqual(len(mandatory_reqs), 2, "Expected 2 MANDATORY requirements")
        
        # Filter by priority
        high_priority_reqs = self.store.filter_requirements(priority=RequirementPriority.HIGH)
        self.assertEqual(len(high_priority_reqs), 1, "Expected 1 HIGH priority requirement")
        
        # Filter by source
        access_control_reqs = self.store.filter_requirements(source="Section 1: Access Control")
        self.assertEqual(len(access_control_reqs), 2, "Expected 2 Access Control requirements")
        
        # Combined filter
        combined_reqs = self.store.filter_requirements(
            category="Authentication",
            req_type="mandatory"
        )
        self.assertEqual(len(combined_reqs), 1, "Expected 1 mandatory Authentication requirement")
    
    def test_delete_requirement(self):
        """Test deleting a requirement"""
        # Add a requirement
        self.store.add_requirement(self.req1)
        
        # Delete the requirement
        result = self.store.delete_requirement(self.req1.id)
        
        # Check the result
        self.assertTrue(result, "Failed to delete requirement")
        
        # Check that the requirement was deleted
        requirements = self.store.get_all_requirements()
        self.assertEqual(len(requirements), 0, "Expected 0 requirements after deletion")
    
    def test_clear_store(self):
        """Test clearing the store"""
        # Add multiple requirements
        self.store.add_requirements([self.req1, self.req2, self.req3])
        
        # Clear the store
        self.store.clear()
        
        # Check that the store is empty
        requirements = self.store.get_all_requirements()
        self.assertEqual(len(requirements), 0, "Expected 0 requirements after clearing")
    
    def test_add_requirements_bulk(self):
        """Test adding multiple requirements at once"""
        # Add multiple requirements
        results = self.store.add_requirements([self.req1, self.req2, self.req3])
        
        # Check the results
        self.assertEqual(len(results), 3, "Expected 3 results")
        self.assertTrue(all(results.values()), "Expected all additions to succeed")
        
        # Check that all requirements were added
        requirements = self.store.get_all_requirements()
        self.assertEqual(len(requirements), 3, "Expected 3 requirements in store")
    
    def test_save_and_load_yaml(self):
        """Test saving and loading requirements to/from YAML"""
        # Add multiple requirements
        self.store.add_requirements([self.req1, self.req2, self.req3])
        
        # Save to YAML
        self.store.save_to_yaml()
        
        # Check that the file was created
        self.assertTrue(self.yaml_path.exists(), "YAML file was not created")
        
        # Create a new store and load from the YAML file
        new_store = RequirementStore(yaml_path=self.yaml_path)
        
        # Check that the requirements were loaded
        requirements = new_store.get_all_requirements()
        self.assertEqual(len(requirements), 3, "Expected 3 requirements after loading")
        
        # Check that all the indexes were created
        self.assertEqual(len(new_store.category_index), 2, "Expected 2 categories")
        self.assertEqual(len(new_store.type_index), 2, "Expected 2 requirement types")
    
    def test_yaml_format(self):
        """Test the format of the generated YAML file"""
        # Add a requirement
        self.store.add_requirement(self.req1)
        
        # Save to YAML
        self.store.save_to_yaml()
        
        # Read the YAML file
        with open(self.yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Check the structure
        self.assertIn("policy_requirements", data, "Missing 'policy_requirements' key")
        self.assertIn("metadata", data, "Missing 'metadata' key")
        
        # Check requirements
        requirements = data["policy_requirements"]
        self.assertEqual(len(requirements), 1, "Expected 1 requirement in YAML")
        self.assertEqual(requirements[0]["id"], self.req1.id)
        
        # Check metadata
        metadata = data["metadata"]
        self.assertIn("last_updated", metadata, "Missing 'last_updated' in metadata")
        self.assertIn("total_requirements", metadata, "Missing 'total_requirements' in metadata")
    
    def test_get_stats(self):
        """Test getting statistics about requirements"""
        # Add multiple requirements
        self.store.add_requirements([self.req1, self.req2, self.req3])
        
        # Get stats
        stats = self.store.get_stats()
        
        # Check the stats
        self.assertEqual(stats["total_requirements"], 3, "Expected 3 total requirements")
        self.assertEqual(stats["by_type"]["mandatory"], 2, "Expected 2 mandatory requirements")
        self.assertEqual(stats["by_type"]["recommended"], 1, "Expected 1 recommended requirement")
        self.assertEqual(stats["by_category"]["Authentication"], 2, "Expected 2 Authentication requirements")
        self.assertEqual(stats["by_category"]["Logging"], 1, "Expected 1 Logging requirement")

class TestThreadSafety(unittest.TestCase):
    """Test thread safety of the requirement store"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for YAML files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.yaml_path = Path(self.temp_dir.name) / "test_requirements.yaml"
        
        # Create the store with the test path
        self.store = RequirementStore(yaml_path=self.yaml_path)
    
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    def test_thread_safety(self):
        """Test concurrent access to the store"""
        # Note: This is a basic test that doesn't actually use multiple threads
        # A more comprehensive test would use the threading module to create
        # multiple threads accessing the store simultaneously
        
        # Create a sample requirement
        req = ComplianceRequirement(
            id="req_001",
            description="Test requirement",
            type=RequirementType.MANDATORY,
            priority=RequirementPriority.MEDIUM,
            source=RequirementSource(document_section="Test"),
            confidence_score=0.9,
            category="Test"
        )
        
        # Add the requirement (this will acquire the lock)
        self.store.add_requirement(req)
        
        # Get the requirement (this will also acquire the lock)
        requirement = self.store.get_requirement(req.id)
        
        # Check that we got the correct requirement
        self.assertIsNotNone(requirement, "Failed to get requirement")
        self.assertEqual(requirement.id, req.id)

# Main function
if __name__ == "__main__":
    unittest.main()