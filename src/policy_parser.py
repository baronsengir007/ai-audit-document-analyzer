"""
Policy Parser Module
Extracts structured compliance requirements from policy documents using LLM.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import re
from datetime import datetime

from llm_wrapper import OllamaWrapper
from llm_error_handler import LLMErrorHandler, LLMErrorType
from document_processor import (
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
    """Structured compliance requirement"""
    id: str
    description: str
    type: RequirementType
    priority: RequirementPriority
    source: RequirementSource
    confidence_score: float
    category: str
    subcategory: Optional[str] = None
    relationships: List[RequirementRelationship] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class PolicyParser:
    """Main class for parsing policy documents and extracting requirements"""
    
    def __init__(self, llm: Optional[OllamaWrapper] = None):
        self.llm = llm or OllamaWrapper()
        self.error_handler = LLMErrorHandler()
        self.logger = logging.getLogger(__name__)
        
        # Initialize document processors
        self.document_processors = {
            '.pdf': extract_text_from_pdf,
            '.docx': extract_text_from_word,
            '.xlsx': extract_text_from_excel,
            '.txt': lambda x: open(x, 'r', encoding='utf-8').read()
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text for LLM processing"""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,;:!?()]', ' ', text)
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text.strip()
    
    def _chunk_text(self, text: str, chunk_size: int = 2000) -> List[str]:
        """Split text into manageable chunks for LLM processing"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if current_size + len(paragraph) > chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(paragraph)
            current_size += len(paragraph)
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _extract_requirements_from_chunk(self, chunk: str, context: Optional[str] = None) -> List[Dict]:
        """Extract requirements from a text chunk using LLM"""
        prompt = f"""
        Extract compliance requirements from the following policy text.
        Format each requirement as a JSON object with these exact fields:
        {{
            "id": "unique_identifier",
            "description": "requirement description",
            "type": "mandatory|recommended|prohibited",
            "priority": "critical|high|medium|low",
            "category": "category name",
            "subcategory": "subcategory name (optional)",
            "keywords": ["keyword1", "keyword2"],
            "source": {{
                "document_section": "section name",
                "context": "surrounding text"
            }}
        }}

        Previous context (if any):
        {context or "None"}

        Policy text to analyze:
        {chunk}

        Return a JSON array of requirement objects. Ensure the response is ONLY the JSON array.
        """
        
        try:
            response = self.llm._make_request(prompt)
            requirements = json.loads(response['response'])
            return requirements
        except Exception as e:
            self.logger.error(f"Error extracting requirements from chunk: {str(e)}")
            return []
    
    def _merge_requirements(self, requirements: List[Dict]) -> List[ComplianceRequirement]:
        """Merge and deduplicate requirements"""
        seen_ids = set()
        merged = []
        
        for req in requirements:
            if req['id'] in seen_ids:
                continue
            
            seen_ids.add(req['id'])
            merged.append(ComplianceRequirement(
                id=req['id'],
                description=req['description'],
                type=RequirementType(req['type']),
                priority=RequirementPriority(req['priority']),
                category=req['category'],
                subcategory=req.get('subcategory'),
                keywords=req.get('keywords', []),
                source=RequirementSource(
                    document_section=req['source']['document_section'],
                    context=req['source'].get('context')
                ),
                confidence_score=0.9  # Default confidence, can be adjusted based on validation
            ))
        
        return merged
    
    def _identify_relationships(self, requirements: List[ComplianceRequirement]) -> None:
        """Identify relationships between requirements"""
        # Create a prompt to identify relationships
        requirements_text = "\n".join([
            f"Requirement {req.id}: {req.description}"
            for req in requirements
        ])
        
        prompt = f"""
        Analyze these requirements and identify relationships between them.
        For each relationship, provide:
        - source requirement ID
        - target requirement ID
        - relationship type (depends_on, conflicts_with, related_to)
        - description of the relationship

        Requirements:
        {requirements_text}

        Return a JSON array of relationship objects.
        """
        
        try:
            response = self.llm._make_request(prompt)
            relationships = json.loads(response['response'])
            
            # Add relationships to requirements
            for rel in relationships:
                source_req = next(
                    (r for r in requirements if r.id == rel['source_id']),
                    None
                )
                if source_req:
                    source_req.relationships.append(
                        RequirementRelationship(
                            target_id=rel['target_id'],
                            relationship_type=rel['type'],
                            description=rel.get('description')
                        )
                    )
        except Exception as e:
            self.logger.error(f"Error identifying relationships: {str(e)}")
    
    def parse_policy_document(self, file_path: Path) -> List[ComplianceRequirement]:
        """
        Parse a policy document and extract compliance requirements
        
        Args:
            file_path: Path to the policy document
            
        Returns:
            List of extracted compliance requirements
        """
        try:
            # Check file type
            file_ext = file_path.suffix.lower()
            if file_ext not in self.document_processors:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Extract text
            text = self.document_processors[file_ext](str(file_path))
            text = self._preprocess_text(text)
            
            # Split into chunks
            chunks = self._chunk_text(text)
            
            # Extract requirements from each chunk
            all_requirements = []
            context = None
            
            for chunk in chunks:
                requirements = self._extract_requirements_from_chunk(chunk, context)
                all_requirements.extend(requirements)
                context = chunk[-500:]  # Keep last 500 chars as context
            
            # Merge and deduplicate requirements
            merged_requirements = self._merge_requirements(all_requirements)
            
            # Identify relationships
            self._identify_relationships(merged_requirements)
            
            return merged_requirements
            
        except Exception as e:
            self.logger.error(f"Error parsing policy document: {str(e)}")
            raise
    
    def save_requirements(self, requirements: List[ComplianceRequirement], output_path: Path) -> None:
        """Save extracted requirements to a JSON file"""
        output_data = {
            "requirements": [
                {
                    "id": req.id,
                    "description": req.description,
                    "type": req.type.value,
                    "priority": req.priority.value,
                    "category": req.category,
                    "subcategory": req.subcategory,
                    "keywords": req.keywords,
                    "source": {
                        "document_section": req.source.document_section,
                        "page_number": req.source.page_number,
                        "line_number": req.source.line_number,
                        "context": req.source.context
                    },
                    "relationships": [
                        {
                            "target_id": rel.target_id,
                            "type": rel.relationship_type,
                            "description": rel.description
                        }
                        for rel in req.relationships
                    ],
                    "confidence_score": req.confidence_score,
                    "metadata": req.metadata
                }
                for req in requirements
            ],
            "metadata": {
                "extraction_date": datetime.now().isoformat(),
                "total_requirements": len(requirements),
                "requirement_types": {
                    req_type.value: sum(1 for r in requirements if r.type == req_type)
                    for req_type in RequirementType
                }
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
