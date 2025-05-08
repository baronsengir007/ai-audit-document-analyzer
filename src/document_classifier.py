"""
Document Classifier Module
Classifies documents based on their content and metadata.
"""

import re
from typing import Dict, Union, Any

# Import interfaces with relative import to match project structure
from .interfaces import Document

class DocumentClassifier:
    """Classifies documents based on their content and metadata."""
    
    def classify(self, document: Union[Document, Dict[str, Any]]) -> str:
        """
        Classify a document based on its content and metadata
        
        Args:
            document: Either a Document object or a dictionary with 'content' and other metadata
            
        Returns:
            The document classification as a string
        """
        # Extract content from either Document object or dictionary
        content = document.content if isinstance(document, Document) else document.get('content', '')
        
        if not content:
            return "unknown"
        
        # Convert content to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        # Check filename first for better accuracy
        filename = document.filename if isinstance(document, Document) else document.get('filename', '')
        filename_lower = filename.lower()
        
        # If filename contains policy, classify as policy_requirements
        if filename_lower and any(kw in filename_lower for kw in ["policy", "policies", "requirement"]):
            return "policy_requirements"
            
        # Use simple keyword matching to determine document type
        if any(kw in content_lower for kw in ["invoice", "payment", "amount", "total", "bill"]):
            return "invoice"
        
        # Check for policy requirements first (more specific)
        if any(kw in content_lower for kw in ["policy document", "security policy", "password policy"]):
            return "policy_requirements"
        
        if any(kw in content_lower for kw in ["questionnaire", "audit", "assessment", "response"]):
            return "audit_rfi"
            
        if any(kw in content_lower for kw in ["project", "timeline", "milestone", "deliverable"]):
            return "project_data"
            
        if any(kw in content_lower for kw in ["checklist", "verify", "confirmation"]):
            return "checklist"
            
        if any(kw in content_lower for kw in ["policy", "requirement", "regulation", "compliance"]):
            return "policy_requirements"
            
        # Default classification
        return "unknown"
    
    def is_complex(self, document: Union[Document, Dict[str, Any]]) -> bool:
        """
        Determine if a document is complex based on content size and structure
        
        Args:
            document: Either a Document object or a dictionary with 'content'
            
        Returns:
            True if the document is considered complex, False otherwise
        """
        # Extract content from either Document object or dictionary
        content = document.content if isinstance(document, Document) else document.get('content', '')
        
        if not content:
            return False
            
        # Complex documents might have:
        # 1. Many sections (indicated by headers)
        # 2. Large content size
        # 3. Tables or structured data
        
        # Check content size
        if len(content) > 5000:
            return True
            
        # Check for multiple sections (headers)
        headers = re.findall(r'(?:\n|^)#+\s+\w+|(?:\n|^)[A-Z][A-Za-z\s]+\n[-=]+', content)
        if len(headers) > 5:
            return True
            
        # Check for tables (simplified check)
        table_indicators = re.findall(r'\|\s*\w+\s*\|', content)
        if len(table_indicators) > 5:
            return True
            
        return False

# Standalone function that uses the DocumentClassifier class
def classify_document(document: Union[Document, Dict[str, Any]]) -> str:
    """
    Classify a document based on its content and metadata.
    This function serves as a convenient wrapper around the DocumentClassifier class.
    
    Args:
        document: Either a Document object or a dictionary with 'content' and metadata
        
    Returns:
        The document classification as a string
    """
    classifier = DocumentClassifier()
    return classifier.classify(document)
