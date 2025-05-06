"""
Requirement Store Module
Stores and manages policy requirements.
"""

import logging
import os
import yaml
import json
from typing import Dict, List, Optional, Union, Set, Any
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from copy import deepcopy
from threading import RLock

from .policy_parser import (
    ComplianceRequirement,
    RequirementType,
    RequirementPriority,
    RequirementSource,
    RequirementRelationship
)

class RequirementValidator:
    """Validates requirement format and content before storage"""
    
    @staticmethod
    def validate_requirement(requirement: ComplianceRequirement) -> List[str]:
        """
        Validate a requirement before storage, checking all required fields 
        and proper formatting.
        
        Args:
            requirement: The ComplianceRequirement object to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not requirement.id:
            errors.append("Requirement ID is required")
        
        if not requirement.description:
            errors.append("Requirement description is required")
        
        # Validate requirement type
        if not requirement.type or requirement.type not in RequirementType:
            errors.append(f"Invalid requirement type: {requirement.type}")
        
        # Validate priority
        if not requirement.priority or requirement.priority not in RequirementPriority:
            errors.append(f"Invalid requirement priority: {requirement.priority}")
        
        # Validate source
        if not requirement.source or not requirement.source.document_section:
            errors.append("Requirement source information is incomplete")
        
        # Validate category
        if not requirement.category:
            errors.append("Requirement category is required")
        
        # Validate confidence score
        if not 0 <= requirement.confidence_score <= 1:
            errors.append(f"Confidence score must be between 0 and 1, got: {requirement.confidence_score}")
        
        # Validate relationships (if any)
        for rel in requirement.relationships:
            if not rel.target_id:
                errors.append("Relationship target ID is required")
            if not rel.relationship_type:
                errors.append("Relationship type is required")
        
        return errors

class RequirementSerializer:
    """Handles serialization and deserialization of requirements for YAML storage"""
    
    @staticmethod
    def _dataclass_to_dict(obj):
        """Convert dataclass objects to dictionaries for serialization"""
        if is_dataclass(obj):
            # Convert dataclass to dict
            result = {}
            for field in obj.__dataclass_fields__:
                value = getattr(obj, field)
                result[field] = RequirementSerializer._dataclass_to_dict(value)
            return result
        elif isinstance(obj, list):
            # Convert list items
            return [RequirementSerializer._dataclass_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            # Convert dict values
            return {k: RequirementSerializer._dataclass_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, RequirementType) or isinstance(obj, RequirementPriority):
            # Convert enum to string value
            return obj.value
        else:
            # Return primitive values as is
            return obj
    
    @staticmethod
    def to_serializable(requirement: ComplianceRequirement) -> Dict:
        """
        Convert a ComplianceRequirement to a YAML-serializable dictionary
        
        Args:
            requirement: ComplianceRequirement object to convert
            
        Returns:
            Dictionary representing the requirement
        """
        return RequirementSerializer._dataclass_to_dict(requirement)
    
    @staticmethod
    def from_dict(data: Dict) -> ComplianceRequirement:
        """
        Convert a dictionary to a ComplianceRequirement object
        
        Args:
            data: Dictionary representation of a requirement
            
        Returns:
            ComplianceRequirement object
        """
        # Create source
        source_data = data.get('source', {})
        source = RequirementSource(
            document_section=source_data.get('document_section', ''),
            page_number=source_data.get('page_number'),
            line_number=source_data.get('line_number'),
            context=source_data.get('context')
        )
        
        # Create relationships
        relationships = []
        for rel_data in data.get('relationships', []):
            rel = RequirementRelationship(
                target_id=rel_data.get('target_id', ''),
                relationship_type=rel_data.get('type', ''),
                description=rel_data.get('description')
            )
            relationships.append(rel)
        
        # Create requirement
        requirement = ComplianceRequirement(
            id=data.get('id', ''),
            description=data.get('description', ''),
            type=RequirementType(data.get('type', 'mandatory')),
            priority=RequirementPriority(data.get('priority', 'medium')),
            source=source,
            confidence_score=data.get('confidence_score', 0.0),
            category=data.get('category', ''),
            subcategory=data.get('subcategory'),
            relationships=relationships,
            keywords=data.get('keywords', []),
            metadata=data.get('metadata', {})
        )
        
        return requirement

class RequirementStore:
    """
    Main class for storing and managing compliance requirements 
    with both in-memory and YAML persistence.
    """
    
    def __init__(self, yaml_path: Optional[Path] = None):
        """
        Initialize the requirement store
        
        Args:
            yaml_path: Optional path to YAML file for persistence
        """
        self.logger = logging.getLogger(__name__)
        self.yaml_path = yaml_path or Path('config/policy_requirements.yaml')
        self.requirements: Dict[str, ComplianceRequirement] = {}
        self.validator = RequirementValidator()
        self.serializer = RequirementSerializer()
        self.lock = RLock()  # For thread safety
        self.last_updated = datetime.now()
        
        # Initialize indexes for efficient querying
        self.category_index: Dict[str, Set[str]] = {}  # category -> set of req_ids
        self.type_index: Dict[str, Set[str]] = {}      # type -> set of req_ids
        self.priority_index: Dict[str, Set[str]] = {}  # priority -> set of req_ids
        self.source_index: Dict[str, Set[str]] = {}    # source doc -> set of req_ids
        
        # Try to load existing requirements if available
        try:
            self.load_from_yaml()
        except (FileNotFoundError, yaml.YAMLError) as e:
            self.logger.info(f"No existing requirements found or error loading: {str(e)}")
    
    def _update_indexes(self, requirement: ComplianceRequirement) -> None:
        """Update search indexes with a requirement"""
        req_id = requirement.id
        
        # Update category index
        category = requirement.category
        if category not in self.category_index:
            self.category_index[category] = set()
        self.category_index[category].add(req_id)
        
        # Update type index
        req_type = requirement.type.value
        if req_type not in self.type_index:
            self.type_index[req_type] = set()
        self.type_index[req_type].add(req_id)
        
        # Update priority index
        priority = requirement.priority.value
        if priority not in self.priority_index:
            self.priority_index[priority] = set()
        self.priority_index[priority].add(req_id)
        
        # Update source index
        source = requirement.source.document_section
        if source not in self.source_index:
            self.source_index[source] = set()
        self.source_index[source].add(req_id)
    
    def _remove_from_indexes(self, requirement: ComplianceRequirement) -> None:
        """Remove a requirement from all indexes"""
        req_id = requirement.id
        
        # Remove from category index
        category = requirement.category
        if category in self.category_index and req_id in self.category_index[category]:
            self.category_index[category].remove(req_id)
        
        # Remove from type index
        req_type = requirement.type.value
        if req_type in self.type_index and req_id in self.type_index[req_type]:
            self.type_index[req_type].remove(req_id)
        
        # Remove from priority index
        priority = requirement.priority.value
        if priority in self.priority_index and req_id in self.priority_index[priority]:
            self.priority_index[priority].remove(req_id)
        
        # Remove from source index
        source = requirement.source.document_section
        if source in self.source_index and req_id in self.source_index[source]:
            self.source_index[source].remove(req_id)
    
    def add_requirement(self, requirement: ComplianceRequirement) -> bool:
        """
        Add a new requirement to the store
        
        Args:
            requirement: ComplianceRequirement to add
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        with self.lock:
            # Validate requirement
            errors = self.validator.validate_requirement(requirement)
            if errors:
                self.logger.error(f"Validation errors for requirement {requirement.id}: {errors}")
                return False
            
            # Check if requirement already exists
            if requirement.id in self.requirements:
                self.logger.warning(f"Requirement with ID {requirement.id} already exists")
                return False
            
            # Add requirement to store
            self.requirements[requirement.id] = deepcopy(requirement)
            
            # Update indexes
            self._update_indexes(requirement)
            
            # Update timestamp
            self.last_updated = datetime.now()
            
            self.logger.info(f"Added requirement {requirement.id}")
            return True
    
    def update_requirement(self, requirement: ComplianceRequirement) -> bool:
        """
        Update an existing requirement
        
        Args:
            requirement: ComplianceRequirement with updated information
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        with self.lock:
            # Validate requirement
            errors = self.validator.validate_requirement(requirement)
            if errors:
                self.logger.error(f"Validation errors for requirement {requirement.id}: {errors}")
                return False
            
            # Check if requirement exists
            if requirement.id not in self.requirements:
                self.logger.warning(f"Requirement with ID {requirement.id} does not exist")
                return False
            
            # Remove from indexes
            old_req = self.requirements[requirement.id]
            self._remove_from_indexes(old_req)
            
            # Update requirement
            self.requirements[requirement.id] = deepcopy(requirement)
            
            # Update indexes
            self._update_indexes(requirement)
            
            # Update timestamp
            self.last_updated = datetime.now()
            
            self.logger.info(f"Updated requirement {requirement.id}")
            return True
    
    def add_or_update_requirement(self, requirement: ComplianceRequirement) -> bool:
        """
        Add a new requirement or update if it already exists
        
        Args:
            requirement: ComplianceRequirement to add or update
            
        Returns:
            bool: True if added/updated successfully, False otherwise
        """
        with self.lock:
            if requirement.id in self.requirements:
                return self.update_requirement(requirement)
            else:
                return self.add_requirement(requirement)
    
    def add_requirements(self, requirements: List[ComplianceRequirement]) -> Dict[str, bool]:
        """
        Add multiple requirements to the store
        
        Args:
            requirements: List of ComplianceRequirement objects to add
            
        Returns:
            Dict mapping requirement IDs to success status
        """
        results = {}
        with self.lock:
            for req in requirements:
                results[req.id] = self.add_or_update_requirement(req)
                
            # If any were added successfully, save to YAML
            if any(results.values()):
                try:
                    self.save_to_yaml()
                except Exception as e:
                    self.logger.error(f"Error saving requirements to YAML: {str(e)}")
            
        return results
    
    def get_requirement(self, requirement_id: str) -> Optional[ComplianceRequirement]:
        """
        Get a requirement by ID
        
        Args:
            requirement_id: ID of the requirement to retrieve
            
        Returns:
            ComplianceRequirement if found, None otherwise
        """
        with self.lock:
            req = self.requirements.get(requirement_id)
            if req:
                return deepcopy(req)
            return None
    
    def get_all_requirements(self) -> List[ComplianceRequirement]:
        """
        Get all requirements in the store
        
        Returns:
            List of all ComplianceRequirement objects
        """
        with self.lock:
            return list(deepcopy(req) for req in self.requirements.values())
    
    def filter_requirements(self, 
                           category: Optional[str] = None,
                           req_type: Optional[Union[str, RequirementType]] = None,
                           priority: Optional[Union[str, RequirementPriority]] = None,
                           source: Optional[str] = None) -> List[ComplianceRequirement]:
        """
        Filter requirements by various criteria
        
        Args:
            category: Filter by category
            req_type: Filter by requirement type (string or enum)
            priority: Filter by priority (string or enum)
            source: Filter by source document section
            
        Returns:
            List of matching ComplianceRequirement objects
        """
        with self.lock:
            # Convert enum parameters to string values if needed
            if isinstance(req_type, RequirementType):
                req_type = req_type.value
            if isinstance(priority, RequirementPriority):
                priority = priority.value
            
            # Start with all requirement IDs
            result_ids = set(self.requirements.keys())
            
            # Apply filters
            if category and category in self.category_index:
                result_ids &= self.category_index[category]
            
            if req_type and req_type in self.type_index:
                result_ids &= self.type_index[req_type]
            
            if priority and priority in self.priority_index:
                result_ids &= self.priority_index[priority]
            
            if source and source in self.source_index:
                result_ids &= self.source_index[source]
            
            # Return matching requirements
            return [deepcopy(self.requirements[req_id]) for req_id in result_ids]
    
    def delete_requirement(self, requirement_id: str) -> bool:
        """
        Delete a requirement by ID
        
        Args:
            requirement_id: ID of the requirement to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        with self.lock:
            if requirement_id not in self.requirements:
                self.logger.warning(f"Requirement with ID {requirement_id} does not exist")
                return False
            
            # Remove from indexes
            req = self.requirements[requirement_id]
            self._remove_from_indexes(req)
            
            # Remove from store
            del self.requirements[requirement_id]
            
            # Update timestamp
            self.last_updated = datetime.now()
            
            self.logger.info(f"Deleted requirement {requirement_id}")
            return True
    
    def clear(self) -> None:
        """Clear all requirements from the store"""
        with self.lock:
            self.requirements.clear()
            self.category_index.clear()
            self.type_index.clear()
            self.priority_index.clear()
            self.source_index.clear()
            self.last_updated = datetime.now()
            self.logger.info("Cleared all requirements")
    
    def save_to_yaml(self, path: Optional[Path] = None) -> None:
        """
        Save requirements to YAML file
        
        Args:
            path: Optional path to save to (defaults to self.yaml_path)
        """
        save_path = path or self.yaml_path
        
        with self.lock:
            # Ensure directory exists
            os.makedirs(save_path.parent, exist_ok=True)
            
            # Convert requirements to serializable format
            requirements_data = []
            for req in self.requirements.values():
                req_dict = self.serializer.to_serializable(req)
                requirements_data.append(req_dict)
            
            # Create output data structure
            output_data = {
                "policy_requirements": requirements_data,
                "metadata": {
                    "last_updated": self.last_updated.isoformat(),
                    "total_requirements": len(self.requirements),
                    "requirement_types": {
                        req_type: len(reqs) 
                        for req_type, reqs in self.type_index.items()
                    }
                }
            }
            
            # Write to YAML file
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(output_data, f, sort_keys=False, indent=2)
            
            self.logger.info(f"Saved {len(self.requirements)} requirements to {save_path}")
    
    def load_from_yaml(self, path: Optional[Path] = None) -> None:
        """
        Load requirements from YAML file
        
        Args:
            path: Optional path to load from (defaults to self.yaml_path)
        """
        load_path = path or self.yaml_path
        
        with self.lock:
            # Clear current data
            self.clear()
            
            # Read YAML file
            with open(load_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data or not isinstance(data, dict):
                self.logger.warning(f"Invalid YAML data in {load_path}")
                return
            
            # Extract requirements data
            requirements_data = data.get("policy_requirements", [])
            if not requirements_data:
                self.logger.info(f"No requirements found in {load_path}")
                return
            
            # Load metadata
            metadata = data.get("metadata", {})
            if "last_updated" in metadata:
                try:
                    self.last_updated = datetime.fromisoformat(metadata["last_updated"])
                except (ValueError, TypeError):
                    self.last_updated = datetime.now()
            
            # Convert and add requirements
            for req_data in requirements_data:
                try:
                    requirement = self.serializer.from_dict(req_data)
                    self.add_requirement(requirement)
                except Exception as e:
                    self.logger.error(f"Error loading requirement: {str(e)}")
            
            self.logger.info(f"Loaded {len(self.requirements)} requirements from {load_path}")
    
    def export_to_json(self, path: Path) -> None:
        """
        Export requirements to a JSON file
        
        Args:
            path: Path to save JSON file
        """
        with self.lock:
            # Convert requirements to serializable format
            requirements_data = []
            for req in self.requirements.values():
                req_dict = self.serializer.to_serializable(req)
                requirements_data.append(req_dict)
            
            # Create output data structure
            output_data = {
                "policy_requirements": requirements_data,
                "metadata": {
                    "last_updated": self.last_updated.isoformat(),
                    "total_requirements": len(self.requirements),
                    "requirement_types": {
                        req_type: len(reqs) 
                        for req_type, reqs in self.type_index.items()
                    }
                }
            }
            
            # Write to JSON file
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Exported {len(self.requirements)} requirements to JSON: {path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored requirements
        
        Returns:
            Dictionary with requirement statistics
        """
        with self.lock:
            return {
                "total_requirements": len(self.requirements),
                "by_type": {
                    req_type: len(reqs) 
                    for req_type, reqs in self.type_index.items()
                },
                "by_priority": {
                    priority: len(reqs) 
                    for priority, reqs in self.priority_index.items()
                },
                "by_category": {
                    category: len(reqs) 
                    for category, reqs in self.category_index.items()
                },
                "last_updated": self.last_updated.isoformat()
            }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    # Create a sample requirement
    source = RequirementSource(document_section="Section 1: Access Control")
    req = ComplianceRequirement(
        id="req_001",
        description="All passwords must be at least 12 characters long",
        type=RequirementType.MANDATORY,
        priority=RequirementPriority.HIGH,
        source=source,
        confidence_score=0.95,
        category="Authentication",
        subcategory="Password Policy",
        keywords=["password", "length", "security"]
    )
    
    # Create requirement store
    store = RequirementStore()
    
    # Add requirement
    store.add_requirement(req)
    
    # Save to YAML
    store.save_to_yaml()
    
    # Load from YAML
    store_2 = RequirementStore()
    print(f"Loaded {len(store_2.get_all_requirements())} requirements")
    
    # Filter requirements
    password_reqs = store_2.filter_requirements(category="Authentication")
    print(f"Found {len(password_reqs)} authentication requirements")