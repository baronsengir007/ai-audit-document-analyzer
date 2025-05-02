from typing import Dict, List, Optional
import json

class ChecklistPromptTemplates:
    """
    A collection of prompt templates for static checklist analysis.
    These templates are designed to work with the OllamaWrapper for document analysis.
    """
    
    @staticmethod
    def get_completeness_check_prompt(document: Dict, checklist_item: Dict) -> str:
        """
        Generate a prompt for checking document completeness against a checklist item.
        
        Args:
            document: Dictionary containing document information
            checklist_item: Dictionary containing checklist item details
            
        Returns:
            str: Formatted prompt for completeness check
        """
        return f"""
        Analyze the following document to determine if it satisfies the completeness requirements:

        DOCUMENT INFORMATION:
        - Filename: {document['filename']}
        - Type: {document['type']}
        - Content: {document['content'][:1000]}...  # First 1000 chars for context

        CHECKLIST REQUIREMENT:
        - ID: {checklist_item['id']}
        - Description: {checklist_item['description']}
        - Required Keywords: {', '.join(checklist_item['required_keywords'])}

        INSTRUCTIONS:
        1. Check if the document contains ALL required keywords
        2. Consider context and meaning, not just exact matches
        3. Look for variations or synonyms of the keywords
        4. Assess if the document fully addresses the requirement

        Return your analysis in this exact JSON format:
        {{
            "satisfied": boolean,
            "explanation": "Detailed explanation of why the requirement is satisfied or not",
            "found_keywords": ["list", "of", "found", "keywords"],
            "missing_keywords": ["list", "of", "missing", "keywords"],
            "confidence_score": float (0.0 to 1.0),
            "suggestions": ["list", "of", "suggestions", "for", "improvement"]
        }}

        Example response:
        {{
            "satisfied": true,
            "explanation": "The document contains all required keywords in appropriate context...",
            "found_keywords": ["keyword1", "keyword2"],
            "missing_keywords": [],
            "confidence_score": 0.95,
            "suggestions": ["Consider adding more detail about X"]
        }}
        """
    
    @staticmethod
    def get_required_fields_prompt(document: Dict, required_fields: List[str]) -> str:
        """
        Generate a prompt for verifying required fields in a document.
        
        Args:
            document: Dictionary containing document information
            required_fields: List of field names that must be present
            
        Returns:
            str: Formatted prompt for required fields verification
        """
        return f"""
        Analyze the following document to verify the presence of required fields:

        DOCUMENT INFORMATION:
        - Filename: {document['filename']}
        - Type: {document['type']}
        - Content: {document['content'][:1000]}...  # First 1000 chars for context

        REQUIRED FIELDS:
        {json.dumps(required_fields, indent=2)}

        INSTRUCTIONS:
        1. Check if each required field is present in the document
        2. Consider both explicit field names and implicit presence
        3. Look for field values in different formats or locations
        4. Assess if the field content is meaningful and complete

        Return your analysis in this exact JSON format:
        {{
            "missing_fields": ["list", "of", "missing", "fields"],
            "present_fields": ["list", "of", "present", "fields"],
            "field_details": [
                {{
                    "field_name": "field1",
                    "is_present": boolean,
                    "location": "where the field was found",
                    "value": "extracted value if present",
                    "confidence": float (0.0 to 1.0)
                }}
            ],
            "overall_completeness": float (0.0 to 1.0),
            "suggestions": ["list", "of", "suggestions", "for", "improvement"]
        }}

        Example response:
        {{
            "missing_fields": ["field3"],
            "present_fields": ["field1", "field2"],
            "field_details": [
                {{
                    "field_name": "field1",
                    "is_present": true,
                    "location": "header section",
                    "value": "example value",
                    "confidence": 0.9
                }}
            ],
            "overall_completeness": 0.67,
            "suggestions": ["Add field3 in the document header"]
        }}
        """
    
    @staticmethod
    def get_document_type_specific_prompt(document: Dict, checklist_item: Dict, doc_type: str, required_fields: List[str]) -> str:
        """
        Generate a type-specific prompt that combines completeness and field checks.
        
        Args:
            document: Dictionary containing document information
            checklist_item: Dictionary containing checklist item details
            doc_type: Type of document (e.g., "invoice", "contract", "report")
            required_fields: List of required field names
            
        Returns:
            str: Formatted prompt for type-specific analysis
        """
        return f"""
        Analyze this {doc_type} document for both completeness and required fields:

        DOCUMENT INFORMATION:
        - Filename: {document['filename']}
        - Type: {doc_type}
        - Content: {document['content'][:1000]}...  # First 1000 chars for context

        CHECKLIST REQUIREMENT:
        - ID: {checklist_item['id']}
        - Description: {checklist_item['description']}
        - Required Keywords: {', '.join(checklist_item['required_keywords'])}

        REQUIRED FIELDS:
        {json.dumps(required_fields, indent=2)}

        INSTRUCTIONS:
        1. Check for required keywords and their context
        2. Verify presence of all required fields
        3. Validate field formats and content
        4. Assess overall document completeness
        5. Provide specific suggestions for improvement

        Return your analysis in this exact JSON format:
        {{
            "satisfied": boolean,
            "completeness_score": float (0.0 to 1.0),
            "keyword_analysis": {{
                "found": ["list", "of", "found", "keywords"],
                "missing": ["list", "of", "missing", "keywords"]
            }},
            "field_analysis": [
                {{
                    "field_name": "actual_field_name",
                    "is_present": boolean,
                    "value": "extracted value",
                    "format_valid": boolean,
                    "confidence": float (0.0 to 1.0)
                }}
            ],
            "suggestions": [
                {{
                    "field": "field_name",
                    "issue": "description of the issue",
                    "recommendation": "specific improvement suggestion"
                }}
            ]
        }}

        Example response:
        {{
            "satisfied": true,
            "completeness_score": 0.95,
            "keyword_analysis": {{
                "found": ["invoice", "date", "amount"],
                "missing": []
            }},
            "field_analysis": [
                {{
                    "field_name": "invoice_number",
                    "is_present": true,
                    "value": "INV-2024-001",
                    "format_valid": true,
                    "confidence": 1.0
                }}
            ],
            "suggestions": [
                {{
                    "field": "description",
                    "issue": "Description is too brief",
                    "recommendation": "Add more details about the services provided"
                }}
            ]
        }}
        """

# Example usage
if __name__ == "__main__":
    # Example document
    example_doc = {
        "filename": "example_invoice.pdf",
        "type": "invoice",
        "content": "Invoice #12345\nDate: 2024-01-01\nAmount: $1000.00\nDescription: Services rendered"
    }
    
    # Example checklist item
    example_checklist = {
        "id": "invoice_requirements",
        "description": "Basic invoice requirements",
        "required_keywords": ["invoice", "date", "amount", "description"]
    }
    
    # Example required fields
    required_fields = ["invoice_number", "date", "amount", "description", "vendor_name"]
    
    # Generate prompts
    completeness_prompt = ChecklistPromptTemplates.get_completeness_check_prompt(
        example_doc, example_checklist
    )
    fields_prompt = ChecklistPromptTemplates.get_required_fields_prompt(
        example_doc, required_fields
    )
    type_specific_prompt = ChecklistPromptTemplates.get_document_type_specific_prompt(
        example_doc, example_checklist, "invoice", required_fields
    )
    
    print("Completeness Check Prompt:")
    print(completeness_prompt)
    print("\nRequired Fields Prompt:")
    print(fields_prompt)
    print("\nType-Specific Prompt:")
    print(type_specific_prompt) 