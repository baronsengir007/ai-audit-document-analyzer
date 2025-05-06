"""
Policy Requirement Manager
Integrates policy parser with requirement storage for a complete workflow.
"""

import logging
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from .interfaces import Document, ComplianceResult
from .policy_parser import PolicyParser, ComplianceRequirement
from .requirement_store import RequirementStore

class PolicyRequirementManager:
    """
    Manages the complete workflow of extracting requirements from policy documents
    and storing them for later use.
    
    This class integrates the PolicyParser for extraction and RequirementStore 
    for storage, providing a unified interface for the entire process.
    """
    
    def __init__(self, yaml_path: str = "config/policy_requirements.yaml", parser: Optional[PolicyParser] = None, store: Optional[RequirementStore] = None):
        """
        Initialize the policy requirement manager
        
        Args:
            yaml_path: Optional path for YAML storage
            parser: Optional PolicyParser instance
            store: Optional RequirementStore instance
        """
        self.logger = logging.getLogger(__name__)
        self.yaml_path = yaml_path
        self.parser = parser or PolicyParser()
        self.store = store or RequirementStore(yaml_path)
    
    def extract_and_store(self, policy_doc_path: Union[str, Path], auto_save: bool = True) -> Dict[str, bool]:
        """
        Extract requirements from a policy document and store them
        
        Args:
            policy_doc_path: Path to policy document
            auto_save: Whether to automatically save to YAML
            
        Returns:
            Dictionary mapping requirement IDs to success status
        """
        self.logger.info(f"Extracting requirements from {file_path}")
        
        # Extract requirements using the parser
        try:
            requirements = self.parser.parse_policy_document(file_path)
            self.logger.info(f"Extracted {len(requirements)} requirements")
            
            # Add metadata to track source file
            for req in requirements:
                if 'source_file' not in req.metadata:
                    req.metadata['source_file'] = str(file_path)
                if 'extraction_date' not in req.metadata:
                    req.metadata['extraction_date'] = datetime.now().isoformat()
            
            # Store the requirements
            result = self.store.add_requirements(requirements)
            
            # Save to YAML if requested
            if auto_save:
                self.store.save_to_yaml()
            
            self.logger.info(f"Stored {sum(1 for v in result.values() if v)} requirements successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting and storing requirements: {str(e)}")
            raise
    
    def get_requirements(self, **filters) -> List[ComplianceRequirement]:
        """
        Get requirements from the store, optionally filtered
        
        Args:
            **filters: Filters to apply (category, type, priority, source)
            
        Returns:
            List of matching requirements
        """
        return self.store.filter_requirements(**filters)
    
    def get_requirement(self, requirement_id: str) -> Optional[ComplianceRequirement]:
        """
        Get a specific requirement by ID
        
        Args:
            requirement_id: ID of the requirement to retrieve
            
        Returns:
            The requirement if found, None otherwise
        """
        return self.store.get_requirement(requirement_id)
    
    def get_all_requirements(self) -> List[ComplianceRequirement]:
        """
        Get all stored requirements
        
        Returns:
            List of all requirements
        """
        return self.store.get_all_requirements()
    
    def save_to_yaml(self, path: Optional[Path] = None) -> None:
        """
        Save requirements to YAML file
        
        Args:
            path: Optional path to save to (defaults to store's path)
        """
        self.store.save_to_yaml(path)
    
    def export_to_json(self, path: Path) -> None:
        """
        Export requirements to JSON file
        
        Args:
            path: Path to save the JSON file
        """
        self.store.export_to_json(path)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored requirements
        
        Returns:
            Dictionary with requirement statistics
        """
        return self.store.get_stats()
    
    def clear(self) -> None:
        """Clear all stored requirements"""
        self.store.clear()

# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    # Create the manager
    manager = PolicyRequirementManager()
    
    # Example: Extract and store requirements from a policy document
    try:
        policy_path = Path("docs/sample_policy.txt")
        if policy_path.exists():
            result = manager.extract_and_store(policy_path)
            print(f"Extracted and stored requirements: {sum(1 for v in result.values() if v)} successful")
            
            # Print statistics
            stats = manager.get_stats()
            print(f"Total requirements: {stats['total_requirements']}")
            print(f"By category: {stats['by_category']}")
            print(f"By priority: {stats['by_priority']}")
        else:
            print(f"Policy file not found: {policy_path}")
    except Exception as e:
        print(f"Error: {str(e)}")