import json
import logging
from llm_wrapper import OllamaWrapper
from prompt_templates import ChecklistPromptTemplates

def test_prompt_templates():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    # Initialize the LLM wrapper
    llm = OllamaWrapper()
    
    # Test document
    test_doc = {
        "filename": "test_invoice.pdf",
        "type": "invoice",
        "content": """
        INVOICE
        Invoice Number: INV-2024-001
        Date: January 15, 2024
        Vendor: ABC Company
        Client: XYZ Corp
        Amount: $1,500.00
        Description: Professional services rendered for Q1 2024
        Payment Terms: Net 30
        """
    }
    
    # Test checklist item
    test_checklist = {
        "id": "invoice_completeness",
        "description": "Basic invoice completeness check",
        "required_keywords": ["invoice", "date", "amount", "description", "payment"]
    }
    
    # Test required fields
    required_fields = [
        "invoice_number",
        "date",
        "vendor_name",
        "client_name",
        "amount",
        "description",
        "payment_terms"
    ]
    
    try:
        # Test completeness check
        logging.info("Testing completeness check prompt...")
        completeness_prompt = ChecklistPromptTemplates.get_completeness_check_prompt(
            test_doc, test_checklist
        )
        completeness_result = llm._make_request(completeness_prompt)
        print("\nCompleteness Check Result:")
        print(json.dumps(json.loads(completeness_result['response']), indent=2))
        
        # Test required fields check
        logging.info("\nTesting required fields prompt...")
        fields_prompt = ChecklistPromptTemplates.get_required_fields_prompt(
            test_doc, required_fields
        )
        fields_result = llm._make_request(fields_prompt)
        print("\nRequired Fields Check Result:")
        print(json.dumps(json.loads(fields_result['response']), indent=2))
        
        # Test type-specific check
        logging.info("\nTesting type-specific prompt...")
        type_specific_prompt = ChecklistPromptTemplates.get_document_type_specific_prompt(
            test_doc, test_checklist, "invoice", required_fields
        )
        type_specific_result = llm._make_request(type_specific_prompt)
        print("\nType-Specific Check Result:")
        print(json.dumps(json.loads(type_specific_result['response']), indent=2))
        
    except Exception as e:
        logging.error(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    test_prompt_templates() 