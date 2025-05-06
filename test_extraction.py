import json
import logging
import requests
from typing import Dict, List

def extract_requirements_from_text(text: str) -> List[Dict]:
    """Extract requirements from text using Ollama."""
    
    prompt = f"""
    Extract all audit and compliance requirements from this policy document.
    Focus on identifying explicit requirements, obligations, and mandatory statements.

    DOCUMENT CONTENT:
    {text}

    INSTRUCTIONS:
    1. Identify all explicit requirements (look for words like "must", "shall", "required", "mandatory")
    2. Identify implicit requirements (statements that imply an obligation)
    3. For each requirement:
       - Extract the exact requirement text
       - Identify key terms and concepts
       - Note any conditions or exceptions
    4. Format each requirement as a structured object

    Return a JSON array where each object has these exact fields:
    {{
        "id": "unique_identifier",
        "requirement_text": "exact text of the requirement",
        "type": "explicit|implicit",
        "keywords": ["list", "of", "key", "terms"],
        "conditions": ["list", "of", "conditions"],
        "confidence": float (0.0 to 1.0)
    }}
    """
    
    system_prompt = """
    You are a specialized AI assistant for extracting compliance requirements from policy documents.
    Your task is to identify and structure all requirements, both explicit and implicit.
    Focus on accuracy and completeness in requirement extraction.
    Return only valid JSON arrays containing requirement objects.
    """
    
    try:
        # Make request to Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        response_text = result['response']
        
        # Try to extract JSON from the response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to find JSON array in the text
            import re
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise
            
    except Exception as e:
        print(f"Error extracting requirements: {str(e)}")
        return []

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    try:
        # Read the sample policy document
        print("Reading sample policy document...")
        with open('docs/sample_policy.md', 'r') as f:
            policy_content = f.read()
        print(f"Successfully read policy document ({len(policy_content)} characters)")
        
        # Extract requirements
        print("\nExtracting requirements from sample policy document...")
        requirements = extract_requirements_from_text(policy_content)
        print(f"Successfully extracted {len(requirements)} requirements")
        
        # Print results
        print("\nExtracted Requirements:")
        print(json.dumps(requirements, indent=2))
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc() 