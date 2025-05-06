"""
Content Analyzer Module
Analyzes document content for classification and validation purposes.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import Counter

@dataclass
class ContentAnalysis:
    """Results of content analysis"""
    document_type: str
    confidence: float
    key_phrases: List[str]
    structure_elements: Dict[str, Any]
    metadata_suggestions: Dict[str, Any]

class ContentAnalyzer:
    """Analyzes document content for classification and validation"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Define common document structure patterns
        self.structure_patterns = {
            "title": r"^#\s+(.+)$",
            "heading": r"^##\s+(.+)$",
            "list_item": r"^[\-\*]\s+(.+)$",
            "table": r"^\|.+\|$",
            "code_block": r"^```[\w]*$"
        }
        
        # Define document type indicators
        self.type_indicators = {
            "policy": [
                "policy", "procedure", "guideline", "standard",
                "requirement", "compliance", "regulation"
            ],
            "report": [
                "report", "analysis", "findings", "conclusion",
                "recommendation", "summary"
            ],
            "contract": [
                "agreement", "contract", "terms", "conditions",
                "party", "signature", "effective date"
            ],
            "technical": [
                "specification", "technical", "design", "implementation",
                "architecture", "system", "component"
            ]
        }
    
    def analyze_content(self, content: str) -> ContentAnalysis:
        """
        Analyze document content for classification and structure
        
        Args:
            content: The document content to analyze
            
        Returns:
            ContentAnalysis object with analysis results
        """
        try:
            # Split content into lines
            lines = content.split('\n')
            
            # Analyze document type
            doc_type, confidence = self._analyze_document_type(content)
            
            # Extract key phrases
            key_phrases = self._extract_key_phrases(content)
            
            # Analyze document structure
            structure = self._analyze_structure(lines)
            
            # Generate metadata suggestions
            metadata = self._generate_metadata_suggestions(content, structure)
            
            return ContentAnalysis(
                document_type=doc_type,
                confidence=confidence,
                key_phrases=key_phrases,
                structure_elements=structure,
                metadata_suggestions=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing content: {str(e)}")
            return ContentAnalysis(
                document_type="unknown",
                confidence=0.0,
                key_phrases=[],
                structure_elements={},
                metadata_suggestions={}
            )
    
    def _analyze_document_type(self, content: str) -> tuple[str, float]:
        """Analyze content to determine document type"""
        content_lower = content.lower()
        type_scores = {}
        
        # Score each document type
        for doc_type, indicators in self.type_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in content_lower:
                    score += 1
            
            type_scores[doc_type] = score / len(indicators)
        
        # Find best matching type
        if not type_scores:
            return "unknown", 0.0
        
        best_type = max(type_scores.items(), key=lambda x: x[1])
        return best_type[0], best_type[1]
    
    def _extract_key_phrases(self, content: str) -> List[str]:
        """Extract key phrases from content"""
        # Split into words and count frequencies
        words = re.findall(r'\w+', content.lower())
        word_counts = Counter(words)
        
        # Filter out common words and get top phrases
        common_words = {'the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'of', 'for'}
        key_phrases = [
            word for word, count in word_counts.most_common(20)
            if word not in common_words and len(word) > 3
        ]
        
        return key_phrases
    
    def _analyze_structure(self, lines: List[str]) -> Dict[str, Any]:
        """Analyze document structure"""
        structure = {
            "title": None,
            "headings": [],
            "lists": [],
            "tables": [],
            "code_blocks": []
        }
        
        current_list = []
        current_table = []
        in_code_block = False
        
        for line in lines:
            # Check for title
            if not structure["title"]:
                title_match = re.match(self.structure_patterns["title"], line)
                if title_match:
                    structure["title"] = title_match.group(1)
                    continue
            
            # Check for headings
            heading_match = re.match(self.structure_patterns["heading"], line)
            if heading_match:
                structure["headings"].append(heading_match.group(1))
                continue
            
            # Check for list items
            list_match = re.match(self.structure_patterns["list_item"], line)
            if list_match:
                current_list.append(list_match.group(1))
                continue
            elif current_list:
                structure["lists"].append(current_list)
                current_list = []
            
            # Check for tables
            if re.match(self.structure_patterns["table"], line):
                current_table.append(line)
                continue
            elif current_table:
                structure["tables"].append(current_table)
                current_table = []
            
            # Check for code blocks
            if re.match(self.structure_patterns["code_block"], line):
                in_code_block = not in_code_block
                if not in_code_block:
                    structure["code_blocks"].append([])
                continue
            elif in_code_block:
                structure["code_blocks"][-1].append(line)
        
        return structure
    
    def _generate_metadata_suggestions(self, content: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata suggestions based on content analysis"""
        suggestions = {}
        
        # Suggest title
        if structure["title"]:
            suggestions["title"] = structure["title"]
        
        # Suggest keywords
        key_phrases = self._extract_key_phrases(content)
        if key_phrases:
            suggestions["keywords"] = key_phrases
        
        # Suggest document type
        doc_type, confidence = self._analyze_document_type(content)
        if doc_type != "unknown":
            suggestions["document_type"] = doc_type
            suggestions["type_confidence"] = confidence
        
        # Suggest structure metadata
        structure_metadata = {
            "has_title": bool(structure["title"]),
            "heading_count": len(structure["headings"]),
            "list_count": len(structure["lists"]),
            "table_count": len(structure["tables"]),
            "code_block_count": len(structure["code_blocks"])
        }
        suggestions["structure"] = structure_metadata
        
        return suggestions 