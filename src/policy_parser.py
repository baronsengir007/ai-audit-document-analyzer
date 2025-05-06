"""
Policy Parser Module
Extracts structured compliance requirements from policy documents using LLM.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime

from .llm_wrapper import OllamaWrapper
from .interfaces import Document
from .document_processor import (
    extract_text_from_pdf,
    extract_text_from_word,
    extract_text_from_excel
)

class RequirementType(str, Enum):
    """Types of compliance requirements"""
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"
    PROHIBITED = "prohibited"

class RequirementPriority(str, Enum):
    """Priority levels for requirements"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class RequirementSource:
    """Source information for a requirement"""
    document_section: str
    page_number: Optional[int] = None
    line_number: Optional[int] = None
    context: Optional[str] = None

@dataclass
class RequirementRelationship:
    """Relationship between requirements"""
    target_id: str
    relationship_type: str  # e.g., "depends_on", "conflicts_with", "related_to"
    description: Optional[str] = None

@dataclass
class ComplianceRequirement:
    """Represents a compliance requirement extracted from a policy document"""
    id: str
    description: str
    category: str
    source_document: str
    keywords: List[str]
    metadata: Dict[str, Any]
    
    @property
    def type(self) -> Optional[RequirementType]:
        """Get the requirement type from metadata"""
        type_value = self.metadata.get('type')
        if type_value:
            try:
                return RequirementType(type_value)
            except ValueError:
                return None
        return None
    
    @property
    def priority(self) -> Optional[RequirementPriority]:
        """Get the requirement priority from metadata"""
        priority_value = self.metadata.get('priority')
        if priority_value:
            try:
                return RequirementPriority(priority_value)
            except ValueError:
                return None
        return None
    
    @property
    def source(self) -> Optional[RequirementSource]:
        """Get the requirement source from metadata"""
        source_dict = self.metadata.get('source')
        if source_dict and isinstance(source_dict, dict):
            return RequirementSource(
                document_section=source_dict.get('document_section', ''),
                page_number=source_dict.get('page_number'),
                line_number=source_dict.get('line_number'),
                context=source_dict.get('context')
            )
        return None
    
    @property
    def confidence_score(self) -> float:
        """Get the confidence score from metadata"""
        return self.metadata.get('confidence_score', 0.0)
    
    @property
    def subcategory(self) -> Optional[str]:
        """Get the subcategory from metadata"""
        return self.metadata.get('subcategory')
    
    @property
    def relationships(self) -> List[RequirementRelationship]:
        """Get the relationships from metadata"""
        rel_list = self.metadata.get('relationships', [])
        result = []
        for rel_dict in rel_list:
            if isinstance(rel_dict, dict):
                result.append(RequirementRelationship(
                    target_id=rel_dict.get('target_id', ''),
                    relationship_type=rel_dict.get('relationship_type', ''),
                    description=rel_dict.get('description')
                ))
        return result

class PolicyParser:
    """Parses policy documents to extract compliance requirements"""
    
    def __init__(self, llm: Optional[OllamaWrapper] = None):
        self.logger = logging.getLogger(__name__)
        self.llm = llm or OllamaWrapper()
        
    def extract_requirements(self, file_path: Union[str, Path]) -> List[ComplianceRequirement]:
        """
        Extract compliance requirements from a policy document
        
        Args:
            file_path: Path to the policy document
            
        Returns:
            List of extracted ComplianceRequirement objects
        """
        try:
            # Read document content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract requirements using LLM
            prompt = f"""
            Please analyze the following policy document and extract all compliance requirements.
            For each requirement, provide:
            1. A unique identifier
            2. A clear description
            3. The category/type
            4. Key terms or phrases
            
            Document content:
            {content}
            
            Please format the output as a JSON array of requirements.
            """
            
            response = self.llm.generate(prompt)
            
            # Parse LLM response
            try:
                requirements_data = json.loads(response)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse LLM response as JSON")
                return []
                
            # Convert to ComplianceRequirement objects
            requirements = []
            for data in requirements_data:
                try:
                    req = ComplianceRequirement(
                        id=data.get('id', ''),
                        description=data.get('description', ''),
                        category=data.get('category', ''),
                        source_document=str(file_path),
                        keywords=data.get('keywords', []),
                        metadata=data.get('metadata', {})
                    )
                    requirements.append(req)
                except Exception as e:
                    self.logger.warning(f"Failed to parse requirement: {e}")
                    continue
                    
            return requirements
            
        except Exception as e:
            self.logger.error(f"Error extracting requirements: {e}")
            return []
            
    def evaluate_requirement(self, document: Document, requirement: ComplianceRequirement) -> Dict[str, Any]:
        """
        Evaluate if a document satisfies a compliance requirement
        
        Args:
            document: Document to evaluate
            requirement: Requirement to check
            
        Returns:
            Dictionary with evaluation results
        """
        try:
            # Prepare prompt for evaluation
            prompt = f"""
            Please evaluate if the following document satisfies the compliance requirement.
            
            Requirement:
            {requirement.description}
            
            Document content:
            {document.content}
            
            Please analyze and provide:
            1. Whether the document is compliant (yes/no)
            2. Your confidence level (0.0 to 1.0)
            3. Explanation of your evaluation
            4. Any relevant quotes or evidence
            
            Format the response as JSON.
            """
            
            response = self.llm.generate(prompt)
            
            # Parse LLM response
            try:
                evaluation = json.loads(response)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse LLM evaluation response as JSON")
                return {
                    "is_compliant": False,
                    "confidence": 0.0,
                    "error": "Failed to parse evaluation response"
                }
                
            return {
                "is_compliant": evaluation.get('is_compliant', False),
                "confidence": evaluation.get('confidence', 0.0),
                "explanation": evaluation.get('explanation', ''),
                "evidence": evaluation.get('evidence', []),
                "requirement_id": requirement.id
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating requirement: {e}")
            return {
                "is_compliant": False,
                "confidence": 0.0,
                "error": str(e)
            }
