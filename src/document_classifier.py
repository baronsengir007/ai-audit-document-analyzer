import json
from pathlib import Path

def classify_document(doc):
    """
    Classify a document based on its content.
    Returns one of: invoice, audit_rfi, project_data, checklist, policy_requirements, unknown
    """
    content = doc["content"].lower()

    # Simple keyword-based classification
    if "invoice" in content or "total" in content or "amount" in content:
        return "invoice"
    elif "audit" in content and ("requirement" in content or "compliance" in content):
        return "audit_rfi"
    elif "project" in content and ("status" in content or "milestone" in content):
        return "project_data"
    elif "checklist" in content:
        return "checklist"
    elif "policy" in content or "requirements" in content:
        return "policy_requirements"
    else:
        return "unknown"

if __name__ == "__main__":
    # Example usage
    test_doc = {
        "filename": "test.pdf",
        "content": "This is an invoice for $100. Total amount due: $100"
    }
    print(f"Classification: {classify_document(test_doc)}")
