"""
Semantic Document Classifier Module
Classifies documents semantically using LLM with document type configurations.
"""

import os
import logging
import yaml
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .llm_wrapper import OllamaWrapper

class SemanticClassifier:
    """
    Classifies documents semantically using an LLM based on predefined document types.
    Uses document_types.yaml configuration to define document types with descriptions and examples.
    """
    
    def __init__(
        self, 
        config_path: str = "config/document_types.yaml",
        llm_model: str = "mistral",
        confidence_threshold: float = 0.7
    ):
        """
        Initialize the semantic classifier.
        
        Args:
            config_path: Path to the document types configuration file
            llm_model: LLM model to use for classification
            confidence_threshold: Minimum confidence threshold for classification
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.confidence_threshold = confidence_threshold
        
        # Load document types configuration
        self.document_types = self._load_document_types()
        self.logger.info(f"Loaded {len(self.document_types)} document types from configuration")
        
        # Initialize LLM wrapper
        self.llm = OllamaWrapper(model=llm_model)
        self.logger.info(f"Initialized LLM wrapper with model: {llm_model}")
    
    def _load_document_types(self) -> List[Dict[str, Any]]:
        """
        Load document types from the configuration file.
        
        Returns:
            List of document type configurations
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config or 'document_types' not in config:
                self.logger.error(f"Invalid or empty document types configuration: {self.config_path}")
                return []
                
            return config['document_types']
            
        except Exception as e:
            self.logger.error(f"Error loading document types configuration: {e}")
            return []
    
    def classify_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a document semantically using the LLM.
        
        Args:
            document: Dictionary containing document information with at least 'content' field
            
        Returns:
            Dictionary with classification results containing:
            - type_id: ID of the classified document type
            - type_name: Name of the classified document type
            - confidence: Confidence score (0-1)
            - rationale: Explanation of the classification
            - evidence: Text snippets from the document supporting the classification
        """
        if not document.get('content'):
            self.logger.warning(f"Empty content in document: {document.get('filename', 'unknown')}")
            return {
                "type_id": "unknown",
                "type_name": "Unknown",
                "confidence": 0.0,
                "rationale": "Document has no content to classify",
                "evidence": []
            }
        
        # Prepare document types for prompt
        type_descriptions = []
        for doc_type in self.document_types:
            examples = "\n".join([f"  - {ex}" for ex in doc_type.get('examples', [])])
            type_descriptions.append(
                f"Type ID: {doc_type['id']}\n"
                f"Type Name: {doc_type['name']}\n"
                f"Description: {doc_type['description']}\n"
                f"Required: {doc_type['required']}\n"
                f"Example content:\n{examples}"
            )
        
        # Create system prompt for classification
        system_prompt = """
        You are an AI assistant specialized in document classification. Your task is to analyze document content 
        and determine the most appropriate document type from a predefined list. Use semantic understanding 
        rather than just keyword matching. Be precise and thorough in your analysis.
        
        For your classification, you should:
        1. Determine the best matching document type
        2. Provide a confidence score (0-1)
        3. Explain your rationale
        4. Include specific text snippets from the document that support your classification
        
        Return your analysis as JSON with these exact fields:
        - type_id: ID of the document type
        - type_name: Name of the document type
        - confidence: Confidence score (0-1)
        - rationale: Explanation of why this type was chosen
        - evidence: Array of text snippets supporting the classification
        """
        
        # Create user prompt for classification
        document_content = document['content']
        # Limit content length to avoid token limits while keeping enough context
        if len(document_content) > 4000:
            document_content = document_content[:4000] + "... [truncated]"
            
        user_prompt = f"""
        Classify the following document based on its content:
        
        Document: {document.get('filename', 'unknown')}
        
        Content:
        {document_content}
        
        Available document types:
        {"-" * 50}
        {"\n\n".join(type_descriptions)}
        {"-" * 50}
        
        Analyze the document content carefully and determine which document type it best matches.
        If the document clearly doesn't match any of the types, classify it as:
        Type ID: unknown
        Type Name: Unknown
        
        Determine your confidence level (0-1) in this classification.
        Provide specific evidence (exact quotes) from the document that supports your classification.
        
        Respond with a JSON object containing these fields exactly:
        {{
            "type_id": "id_of_document_type",
            "type_name": "Name of Document Type",
            "confidence": 0.XX,
            "rationale": "Explanation of why this classification was chosen",
            "evidence": ["Evidence text 1", "Evidence text 2", ...]
        }}
        """
        
        try:
            # Make request to LLM
            response = self.llm._make_request(user_prompt, system_prompt)
            response_text = response.get('response', '')
            
            # Parse JSON from response
            try:
                # First try direct parsing
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON with regex
                import re
                json_match = re.search(r'({.*})', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    raise ValueError("Could not extract JSON from LLM response")
            
            # Validate required fields
            required_fields = ["type_id", "type_name", "confidence", "rationale", "evidence"]
            for field in required_fields:
                if field not in result:
                    self.logger.warning(f"Missing field '{field}' in LLM response, adding default value")
                    if field == "evidence":
                        result[field] = []
                    elif field == "confidence":
                        result[field] = 0.0
                    else:
                        result[field] = "unknown"
            
            # Ensure confidence is a float between 0 and 1
            try:
                result["confidence"] = float(result["confidence"])
                if result["confidence"] < 0 or result["confidence"] > 1:
                    self.logger.warning(f"Confidence score out of range: {result['confidence']}, clamping to [0,1]")
                    result["confidence"] = max(0, min(1, result["confidence"]))
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid confidence value: {result.get('confidence')}, defaulting to 0")
                result["confidence"] = 0.0
            
            # Ensure evidence is a list
            if not isinstance(result["evidence"], list):
                self.logger.warning("Evidence field is not a list, converting to list")
                result["evidence"] = [str(result["evidence"])]
            
            # Log classification result
            self.logger.info(
                f"Classified document '{document.get('filename', 'unknown')}' as "
                f"'{result['type_name']}' with confidence {result['confidence']:.2f}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error classifying document: {e}")
            return {
                "type_id": "unknown",
                "type_name": "Unknown",
                "confidence": 0.0,
                "rationale": f"Error during classification: {str(e)}",
                "evidence": []
            }
    
    def batch_classify(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify a batch of documents.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of document dictionaries with classification results added
        """
        self.logger.info(f"Batch classifying {len(documents)} documents")
        
        classified_documents = []
        for doc in documents:
            # Skip if already classified with confidence above threshold
            if (doc.get('classification_result') and 
                doc['classification_result'].get('confidence', 0) >= self.confidence_threshold):
                self.logger.info(f"Document already classified: {doc.get('filename', 'unknown')}")
                classified_documents.append(doc)
                continue
                
            # Classify document
            classification = self.classify_document(doc)
            
            # Add classification to document
            doc_copy = doc.copy()
            doc_copy['classification_result'] = classification
            classified_documents.append(doc_copy)
        
        return classified_documents
    
    def get_document_types(self, required_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get the list of document types.
        
        Args:
            required_only: If True, only return required document types
            
        Returns:
            List of document type dictionaries
        """
        if required_only:
            return [doc_type for doc_type in self.document_types if doc_type.get('required', False)]
        return self.document_types


# Standalone function that uses the SemanticClassifier class
def classify_document_semantically(
    document: Dict[str, Any],
    config_path: str = "config/document_types.yaml",
    llm_model: str = "mistral"
) -> Dict[str, Any]:
    """
    Classify a document semantically using the SemanticClassifier.
    
    Args:
        document: Dictionary containing document information
        config_path: Path to document types configuration
        llm_model: LLM model to use
        
    Returns:
        Dictionary with classification results
    """
    classifier = SemanticClassifier(config_path=config_path, llm_model=llm_model)
    return classifier.classify_document(document)