"""
LLM Wrapper Module

Provides interface to LLM models for document classification with robust error handling
and structured response formatting.
"""

import requests
import json
import logging
import re
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

class OllamaWrapper:
    """
    A wrapper class for interacting with the Ollama local LLM API.
    Focused on document classification with structured JSON response handling.
    """
    
    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama wrapper.
        
        Args:
            model: The model name to use (default: "mistral")
            base_url: The base URL for the Ollama API (default: "http://localhost:11434")
        """
        self.model = model
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized OllamaWrapper with model: {model}")
    
    def _make_request(self, user_prompt: str, system_prompt: Optional[str] = None) -> Dict:
        """
        Make a request to the Ollama API.
        
        Args:
            user_prompt: The user prompt to send to the model
            system_prompt: Optional system prompt to set context
            
        Returns:
            Dict containing the model's response
        """
        try:
            payload = {
                "model": self.model,
                "prompt": user_prompt,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            # Log request details at debug level
            self.logger.debug(f"Sending request to Ollama API with model: {self.model}")
            self.logger.debug(f"System prompt: {system_prompt[:100]}..." if system_prompt else "No system prompt")
            self.logger.debug(f"User prompt: {user_prompt[:100]}...")
            
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout when connecting to Ollama API")
            raise TimeoutError("LLM request timed out. Please ensure Ollama is running and not overloaded.")
            
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Could not connect to Ollama API at {self.api_url}")
            raise ConnectionError(f"Could not connect to Ollama at {self.api_url}. Please ensure Ollama is running.")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request to Ollama API: {e}")
            raise
    
    def extract_json_from_text(self, text: str) -> Dict:
        """
        Extract a JSON object from text content.
        
        Args:
            text: Text content that may contain a JSON object
            
        Returns:
            Extracted JSON object as a dictionary
            
        Raises:
            ValueError: If no valid JSON could be extracted
        """
        try:
            # First try direct parsing
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON object in text
            json_pattern = r'({.*})'
            json_match = re.search(json_pattern, text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON array in text
            array_pattern = r'(\[.*\])'
            array_match = re.search(array_pattern, text, re.DOTALL)
            if array_match:
                try:
                    return json.loads(array_match.group(1))
                except json.JSONDecodeError:
                    pass
                    
        # If all extraction attempts fail
        raise ValueError(f"Could not extract valid JSON from response: {text[:100]}...")
    
    def classify_document(self, document: Dict[str, Any], document_types: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classify a document against available document types.
        
        Args:
            document: Dictionary containing document information (filename, content)
            document_types: List of document type definitions
            
        Returns:
            Dictionary containing classification results with standard fields:
            - type_id: ID of the classified document type
            - type_name: Name of the classified document type
            - confidence: Confidence score (0-1)
            - rationale: Explanation of the classification
            - evidence: Text snippets supporting the classification
        """
        if not document.get('content'):
            self.logger.warning(f"Empty content in document: {document.get('filename', 'unknown')}")
            return self._create_default_classification("Document has no content to classify")
        
        if not document_types:
            self.logger.warning("No document types provided for classification")
            return self._create_default_classification("No document types available for classification")
        
        # Prepare document types for prompt
        type_descriptions = []
        for doc_type in document_types:
            example_text = ""
            if 'examples' in doc_type and doc_type['examples']:
                examples = "\n".join([f"  - {ex}" for ex in doc_type['examples']])
                example_text = f"Example content:\n{examples}"
            
            type_descriptions.append(
                f"Type ID: {doc_type['id']}\n"
                f"Type Name: {doc_type['name']}\n"
                f"Description: {doc_type['description']}\n"
                f"Required: {doc_type.get('required', False)}\n"
                f"{example_text}"
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
            response = self._make_request(user_prompt, system_prompt)
            response_text = response.get('response', '')
            
            # Parse JSON from response
            try:
                result = self.extract_json_from_text(response_text)
            except ValueError as e:
                self.logger.error(f"Failed to extract JSON from LLM response: {e}")
                return self._create_default_classification(f"Error parsing LLM response: {str(e)}")
            
            # Validate and sanitize result
            return self._validate_classification_result(result)
            
        except Exception as e:
            self.logger.error(f"Error classifying document: {e}")
            return self._create_default_classification(f"Error during classification: {str(e)}")
    
    def _validate_classification_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize classification result.
        
        Args:
            result: Raw classification result from LLM
            
        Returns:
            Validated and sanitized classification result
        """
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
        
        return result
    
    def _create_default_classification(self, reason: str) -> Dict[str, Any]:
        """
        Create a default classification result.
        
        Args:
            reason: Reason for using default classification
            
        Returns:
            Default classification result
        """
        return {
            "type_id": "unknown",
            "type_name": "Unknown",
            "confidence": 0.0,
            "rationale": reason,
            "evidence": []
        }
    
    def analyze_document(self, document: Dict, checklist_item: Dict) -> Dict:
        """
        Analyze a document against a specific checklist item.
        
        Args:
            document: Dictionary containing document information
            checklist_item: Dictionary containing checklist item details
            
        Returns:
            Dict containing analysis results
        """
        prompt = f"""
        Analyze the following document against this checklist item:
        
        Document: {document['filename']}
        Type: {document.get('type', 'unknown')}
        Content: {document['content'][:1000]}...  # First 1000 chars for context
        
        Checklist Item:
        - ID: {checklist_item['id']}
        - Description: {checklist_item['description']}
        - Required Keywords: {', '.join(checklist_item.get('required_keywords', []))}
        
        Please analyze if the document satisfies this checklist item.
        Return your analysis in JSON format with these fields:
        - satisfied: boolean
        - explanation: string
        - found_keywords: list of strings
        - missing_keywords: list of strings
        """
        
        system_prompt = """
        You are an AI assistant specialized in document analysis and classification.
        Your task is to analyze documents against specific checklist items and determine if they satisfy the requirements.
        Be thorough and precise in your analysis.
        """
        
        try:
            response = self._make_request(prompt, system_prompt)
            response_text = response.get('response', '')
            
            try:
                result = self.extract_json_from_text(response_text)
                return result
            except ValueError as e:
                self.logger.error(f"Failed to extract JSON from LLM response: {e}")
                return {
                    "satisfied": False,
                    "explanation": "Error parsing LLM response",
                    "found_keywords": [],
                    "missing_keywords": checklist_item.get('required_keywords', [])
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing document: {e}")
            return {
                "satisfied": False,
                "explanation": f"Error during analysis: {str(e)}",
                "found_keywords": [],
                "missing_keywords": checklist_item.get('required_keywords', [])
            }
    
    def extract_policy_requirements(self, policy_document: Dict) -> List[Dict]:
        """
        Extract compliance requirements from a policy document.
        
        Args:
            policy_document: Dictionary containing policy document information
            
        Returns:
            List of dictionaries containing extracted requirements
        """
        prompt = f"""
        Extract all audit and compliance requirements from this policy document and format them as a JSON array.

        Document: {policy_document['filename']}
        Content: {policy_document['content'][:2000]}...  # First 2000 chars for context
        
        Return a JSON array where each object has these exact fields:
        {{
            "id": "unique_identifier",
            "description": "requirement description",
            "required_keywords": ["keyword1", "keyword2"]
        }}

        Ensure the response is ONLY the JSON array, with no additional text.
        Example format:
        [
            {{
                "id": "req_1",
                "description": "Document must have a title",
                "required_keywords": ["title", "heading"]
            }},
            {{
                "id": "req_2",
                "description": "Document must be dated",
                "required_keywords": ["date", "dated"]
            }}
        ]
        """
        
        system_prompt = """
        You are a JSON-focused AI assistant. Your responses must be valid JSON arrays containing requirement objects.
        Each object must have exactly three fields: id (string), description (string), and required_keywords (array of strings).
        Do not include any explanatory text - output only the JSON array.
        """
        
        try:
            response = self._make_request(prompt, system_prompt)
            response_text = response.get('response', '')
            
            try:
                result = self.extract_json_from_text(response_text)
                return result if isinstance(result, list) else []
            except ValueError as e:
                self.logger.error(f"Failed to extract JSON from LLM response: {e}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error extracting policy requirements: {e}")
            return []

# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    try:
        # Initialize the wrapper
        llm = OllamaWrapper()
        logging.info("Successfully initialized OllamaWrapper")
        
        # Example document and document types
        example_doc = {
            "filename": "privacy_policy.pdf",
            "content": "This document outlines our privacy policy and how we handle user data. Personal information is collected only with consent and stored securely. Users may request deletion of their data at any time."
        }
        
        example_types = [
            {
                "id": "privacy_policy",
                "name": "Privacy Policy",
                "description": "Document explaining how user data is collected, stored, and protected",
                "required": True,
                "examples": ["User data handling", "Data privacy procedures", "GDPR compliance"]
            },
            {
                "id": "security_policy",
                "name": "Security Policy",
                "description": "Document outlining security measures and protocols",
                "required": True,
                "examples": ["Password requirements", "Access controls", "Security procedures"]
            }
        ]
        
        # Test document classification
        logging.info("Testing document classification...")
        result = llm.classify_document(example_doc, example_types)
        print("\nDocument Classification Result:")
        print(json.dumps(result, indent=2))
        
    except requests.exceptions.ConnectionError:
        logging.error("Could not connect to Ollama. Please make sure Ollama is running on http://localhost:11434")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")