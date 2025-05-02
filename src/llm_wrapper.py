import requests
import json
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

class OllamaWrapper:
    """
    A wrapper class for interacting with the Ollama local LLM API.
    Supports both static checklist validation and dynamic policy analysis.
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
        logging.info(f"Initialized OllamaWrapper with model: {model}")
    
    def _make_request(self, prompt: str, system_prompt: Optional[str] = None) -> Dict:
        """
        Make a request to the Ollama API.
        
        Args:
            prompt: The user prompt to send to the model
            system_prompt: Optional system prompt to set context
            
        Returns:
            Dict containing the model's response
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request to Ollama API: {e}")
            raise
    
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
        Type: {document['type']}
        Content: {document['content'][:1000]}...  # First 1000 chars for context
        
        Checklist Item:
        - ID: {checklist_item['id']}
        - Description: {checklist_item['description']}
        - Required Keywords: {', '.join(checklist_item['required_keywords'])}
        
        Please analyze if the document satisfies this checklist item.
        Return your analysis in JSON format with these fields:
        - satisfied: boolean
        - explanation: string
        - found_keywords: list of strings
        - missing_keywords: list of strings
        """
        
        system_prompt = """
        You are an AI assistant specialized in document analysis and compliance checking.
        Your task is to analyze documents against specific checklist items and determine if they satisfy the requirements.
        Be thorough and precise in your analysis.
        """
        
        try:
            response = self._make_request(prompt, system_prompt)
            return json.loads(response['response'])
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"Error parsing LLM response: {e}")
            return {
                "satisfied": False,
                "explanation": "Error analyzing document",
                "found_keywords": [],
                "missing_keywords": checklist_item['required_keywords']
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
            # Try to extract JSON from the response if it's embedded in text
            response_text = response['response']
            try:
                # First try direct JSON parsing
                return json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try to find JSON array in the text
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                raise
        except Exception as e:
            logging.error(f"Error parsing LLM response: {str(e)}")
            logging.debug(f"Raw response: {response_text}")
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
        
        # Example document and checklist item
        example_doc = {
            "filename": "example.pdf",
            "type": "pdf",
            "content": "This is an example document content that contains the word 'example' and 'test' but not 'missing'."
        }
        
        example_checklist = {
            "id": "example_1",
            "description": "Example checklist item",
            "required_keywords": ["example", "test", "missing"]
        }
        
        # Test document analysis
        logging.info("Testing document analysis...")
        result = llm.analyze_document(example_doc, example_checklist)
        print("\nDocument Analysis Result:")
        print(json.dumps(result, indent=2))
        
        # Test policy requirement extraction
        logging.info("Testing policy requirement extraction...")
        policy_doc = {
            "filename": "policy.pdf",
            "content": "This is an example policy document. All documents must contain: 1) A title, 2) A date, 3) A signature. Keywords to look for: title, date, signature."
        }
        
        requirements = llm.extract_policy_requirements(policy_doc)
        print("\nExtracted Policy Requirements:")
        print(json.dumps(requirements, indent=2))
        
    except requests.exceptions.ConnectionError:
        logging.error("Could not connect to Ollama. Please make sure Ollama is running on http://localhost:11434")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}") 