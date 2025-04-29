import json
from pathlib import Path

# Load the normalized documents
with open("outputs/normalized_docs.json", "r", encoding="utf-8") as f:
    documents = json.load(f)

def classify_document(doc):
    content = doc["content"].lower()

    # Simple keyword-based classification
    if "factuur" in content or "kpn" in content:
        return "invoice"
    elif "request for information" in content and "audit" in content:
        return "audit_rfi"
    elif "epic" in content or "change" in content or "state" in content:
        return "project_data"
    elif "checklist" in content:
        return "checklist"
    elif "policy" in content or "requirements" in content:
        return "policy_requirements"
    else:
        return "unknown"

# Classify and print results
print("\n--- Document Classification Results ---\n")
for doc in documents:
    classification = classify_document(doc)
    print(f"{doc['filename']}: {classification}")
