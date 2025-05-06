import json
import logging
import os
import time
import asyncio
from typing import Dict, List, Optional, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from .llm_wrapper import OllamaWrapper

class PolicyRequirementExtractor:
    """
    A class for extracting compliance requirements from policy documents using LLM.
    Handles various document types, implements chunking strategies, and provides
    structured output of extracted requirements.
    """
    
    def __init__(self, llm_wrapper: OllamaWrapper, chunk_size: int = 2000, 
                 batch_size: int = 5, rate_limit: float = 1.0):
        """
        Initialize the policy requirement extractor.
        
        Args:
            llm_wrapper: An instance of OllamaWrapper for LLM interactions
            chunk_size: Maximum size of document chunks to process at once
            batch_size: Number of chunks to process in parallel
            rate_limit: Minimum time (in seconds) between LLM calls
        """
        self.llm = llm_wrapper
        self.chunk_size = chunk_size
        self.batch_size = batch_size
        self.rate_limit = rate_limit
        self.logger = logging.getLogger(__name__)
        self.last_request_time = 0
    
    def _chunk_document(self, text: str) -> List[str]:
        """Split document into chunks while preserving paragraph boundaries when possible."""
        # Handle the case where the text might have repeating patterns
        if '\n\n' in text:
            paragraphs = text.split('\n\n')
        else:
            paragraphs = [text]
            
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Handle paragraphs larger than chunk_size by splitting them
            if len(para) > self.chunk_size:
                # If we have content in the current chunk, add it first
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split the large paragraph into smaller chunks
                for i in range(0, len(para), self.chunk_size):
                    para_chunk = para[i:i + self.chunk_size]
                    chunks.append(para_chunk)
                
                continue
            
            # Check if adding this paragraph would exceed the chunk size
            # Include the size of paragraph separators in calculation
            separator_size = 2 if current_chunk else 0  # '\n\n' is 2 chars
            if current_size + len(para) + separator_size > self.chunk_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(para)
            current_size += len(para) + separator_size
        
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            # Final safety check to ensure no chunk exceeds the limit
            if len(chunk_text) > self.chunk_size:
                # Split the oversized chunk into smaller pieces
                for i in range(0, len(chunk_text), self.chunk_size):
                    chunks.append(chunk_text[i:i + self.chunk_size])
            else:
                chunks.append(chunk_text)
        
        # Ensure no chunks exceed the limit as a final verification
        result_chunks = []
        for chunk in chunks:
            if len(chunk) > self.chunk_size:
                # Split any remaining oversized chunks
                for i in range(0, len(chunk), self.chunk_size):
                    result_chunks.append(chunk[i:i + self.chunk_size])
            else:
                result_chunks.append(chunk)
                
        return result_chunks
    
    async def _process_chunk(self, chunk: str, context: Dict) -> List[Dict]:
        """Process a single chunk with rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last)
        
        self.last_request_time = time.time()
        return self._extract_requirements_from_chunk(chunk, context)
    
    def _extract_requirements_from_chunk(self, chunk: str, context: Dict) -> List[Dict]:
        """
        Extract requirements from a single document chunk.
        
        Args:
            chunk: The document chunk to analyze
            context: Additional context about the document
            
        Returns:
            List of extracted requirements
        """
        prompt = f"""
        Extract all audit and compliance requirements from this policy document chunk.
        Focus on identifying explicit requirements, obligations, and mandatory statements.

        DOCUMENT CONTEXT:
        - Filename: {context.get('filename', 'Unknown')}
        - Type: {context.get('type', 'Unknown')}
        - Section: {context.get('section', 'Main Content')}

        DOCUMENT CHUNK:
        {chunk}

        INSTRUCTIONS:
        1. Identify all explicit requirements (look for words like "must", "shall", "required", "mandatory")
        2. Identify implicit requirements (statements that imply an obligation)
        3. For each requirement:
           - Extract the exact requirement text
           - Identify key terms and concepts
           - Note any conditions or exceptions
           - Determine if it's a primary or supporting requirement
        4. Format each requirement as a structured object

        Return a JSON array where each object has these exact fields:
        {{
            "id": "unique_identifier",
            "requirement_text": "exact text of the requirement",
            "type": "explicit|implicit",
            "keywords": ["list", "of", "key", "terms"],
            "conditions": ["list", "of", "conditions"],
            "confidence": float (0.0 to 1.0),
            "is_primary": boolean
        }}

        Example format:
        [
            {{
                "id": "req_1",
                "requirement_text": "All documents must be reviewed by a supervisor",
                "type": "explicit",
                "keywords": ["review", "supervisor"],
                "conditions": [],
                "confidence": 0.95,
                "is_primary": true
            }}
        ]
        """
        
        system_prompt = """
        You are a specialized AI assistant for extracting compliance requirements from policy documents.
        Your task is to identify and structure all requirements, both explicit and implicit.
        Focus on accuracy and completeness in requirement extraction.
        Return only valid JSON arrays containing requirement objects.
        """
        
        try:
            response = self.llm._make_request(prompt, system_prompt)
            response_text = response['response']
            
            # Try to extract JSON from the response
            try:
                requirements = json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try to find JSON array in the text
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    requirements = json.loads(json_match.group())
                else:
                    raise
            
            # Post-process requirements
            processed_requirements = []
            for req in requirements:
                # Validate and clean requirement text
                req['requirement_text'] = req['requirement_text'].strip()
                if not req['requirement_text']:
                    continue
                
                # Ensure required fields
                if 'is_primary' not in req:
                    req['is_primary'] = req['type'] == 'explicit'
                
                # Clean keywords
                req['keywords'] = [k.strip().lower() for k in req['keywords'] if k.strip()]
                
                # Clean conditions
                req['conditions'] = [c.strip() for c in req['conditions'] if c.strip()]
                
                processed_requirements.append(req)
            
            return processed_requirements
                
        except Exception as e:
            self.logger.error(f"Error extracting requirements from chunk: {str(e)}")
            return []
    
    async def extract_requirements(self, document: Dict) -> List[Dict]:
        """
        Extract all requirements from a policy document.
        
        Args:
            document: Dictionary containing document information
            
        Returns:
            List of extracted requirements
        """
        self.logger.info(f"Starting requirement extraction for document: {document['filename']}")
        
        # Split document into chunks
        chunks = self._chunk_document(document['content'])
        self.logger.info(f"Split document into {len(chunks)} chunks")
        
        all_requirements = []
        seen_requirements = set()
        
        # Process chunks in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            tasks = []
            
            for j, chunk in enumerate(batch):
                context = {
                    'filename': document['filename'],
                    'type': document.get('type', 'Unknown'),
                    'section': f"Chunk {i+j+1}"
                }
                tasks.append(self._process_chunk(chunk, context))
            
            # Wait for all tasks in batch to complete
            batch_results = await asyncio.gather(*tasks)
            
            # Process results
            for chunk_requirements in batch_results:
                for req in chunk_requirements:
                    req_text = req['requirement_text']
                    if req_text not in seen_requirements:
                        seen_requirements.add(req_text)
                        all_requirements.append(req)
        
        self.logger.info(f"Extracted {len(all_requirements)} unique requirements")
        return all_requirements
    
    def validate_requirements(self, requirements: List[Dict]) -> Dict:
        """
        Validate the extracted requirements for completeness and quality.
        
        Args:
            requirements: List of extracted requirements
            
        Returns:
            Dictionary containing validation results
        """
        validation_results = {
            'total_requirements': len(requirements),
            'explicit_requirements': sum(1 for r in requirements if r['type'] == 'explicit'),
            'implicit_requirements': sum(1 for r in requirements if r['type'] == 'implicit'),
            'primary_requirements': sum(1 for r in requirements if r['is_primary']),
            'average_confidence': sum(r['confidence'] for r in requirements) / len(requirements) if requirements else 0,
            'issues': []
        }
        
        # Check for potential issues
        for req in requirements:
            if not req['keywords']:
                validation_results['issues'].append({
                    'requirement_id': req['id'],
                    'issue': 'No keywords identified',
                    'severity': 'warning'
                })
            
            if req['confidence'] < 0.5:
                validation_results['issues'].append({
                    'requirement_id': req['id'],
                    'issue': 'Low confidence in requirement extraction',
                    'severity': 'warning'
                })
            
            if req['type'] == 'implicit' and req['confidence'] > 0.9:
                validation_results['issues'].append({
                    'requirement_id': req['id'],
                    'issue': 'High confidence for implicit requirement',
                    'severity': 'warning'
                })
        
        return validation_results

# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    try:
        # Initialize the LLM wrapper
        print("Initializing LLM wrapper...")
        llm = OllamaWrapper()
        
        # Initialize the extractor
        print("Initializing policy requirement extractor...")
        extractor = PolicyRequirementExtractor(llm, batch_size=3, rate_limit=0.5)
        
        # Read the sample policy document
        print("Reading sample policy document...")
        try:
            with open('docs/sample_policy.md', 'r') as f:
                policy_content = f.read()
            print(f"Successfully read policy document ({len(policy_content)} characters)")
        except FileNotFoundError:
            print("Error: Could not find docs/sample_policy.md")
            print("Current working directory:", os.getcwd())
            print("Files in current directory:", os.listdir())
            raise
        
        # Create policy document
        policy_doc = {
            "filename": "sample_policy.md",
            "type": "policy",
            "content": policy_content
        }
        
        # Extract requirements
        print("\nExtracting requirements from sample policy document...")
        try:
            requirements = asyncio.run(extractor.extract_requirements(policy_doc))
            print(f"Successfully extracted {len(requirements)} requirements")
        except Exception as e:
            print(f"Error extracting requirements: {str(e)}")
            raise
        
        # Validate requirements
        print("\nValidating extracted requirements...")
        try:
            validation = extractor.validate_requirements(requirements)
            print("Successfully validated requirements")
        except Exception as e:
            print(f"Error validating requirements: {str(e)}")
            raise
        
        # Print results
        print("\nExtracted Requirements:")
        print(json.dumps(requirements, indent=2))
        
        print("\nValidation Results:")
        print(json.dumps(validation, indent=2))
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc() 