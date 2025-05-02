import json
import yaml
from pathlib import Path
import logging

# 1. Read normalized_docs.json and checklist.yaml
with open("outputs/normalized_docs.json", "r", encoding="utf-8") as f:
    documents = json.load(f)

with open("config/checklist.yaml", "r", encoding="utf-8") as f:
    checklist = yaml.safe_load(f)["audit_completeness_checklist"]

# 2. Match classified document types to checklist categories
type_to_checklist_id = {
    "pdf": "invoices",
    "excel": "project_data",
    "word": "audit_rfi",
}

# Build a mapping from checklist id to required keywords
checklist_map = {item["id"]: item["required_keywords"] for item in checklist}

def validate_document(doc):
    doc_type = doc.get("type")
    checklist_id = type_to_checklist_id.get(doc_type)
    if not checklist_id or checklist_id not in checklist_map:
        return {"status": "unknown type", "missing": [], "present": []}
    required_keywords = checklist_map[checklist_id]
    content = doc["content"].lower()
    present = [kw for kw in required_keywords if kw.lower() in content]
    missing = [kw for kw in required_keywords if kw.lower() not in content]
    status = "complete" if not missing else "incomplete"
    return {"status": status, "missing": missing, "present": present}

# 3. For each document, scan for required keywords in content
report = []
for doc in documents:
    result = validate_document(doc)
    print(f"{doc['filename']} ({doc['type']}): {result['status']}")
    if result["missing"]:
        print("  ✗ Missing:", ", ".join(result["missing"]))
    if result["present"]:
        print("  ✓ Present:", ", ".join(result["present"]))
    report.append({"filename": doc["filename"], **result})

# 4. Save the report as JSON
with open("outputs/checklist_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

def scan_and_report_keywords(documents, checklist_map, type_to_checklist_id):
    """
    Scans each document's content for required keywords and reports results.
    Returns a list of dicts: [{doc, checklist_id, present_keywords, missing_keywords}, ...]
    """
    results = []
    for doc in documents:
        doc_type = doc.get("type")
        checklist_id = type_to_checklist_id.get(doc_type)
        if not checklist_id or checklist_id not in checklist_map:
            logging.warning(f"No checklist category found for document '{doc['filename']}' (type: {doc_type}).")
            continue
        required_keywords = checklist_map[checklist_id]
        content = doc["content"].lower()
        present = [kw for kw in required_keywords if kw.lower() in content]
        missing = [kw for kw in required_keywords if kw.lower() not in content]
        results.append({
            "document": doc,
            "checklist_id": checklist_id,
            "present_keywords": present,
            "missing_keywords": missing
        })
    return results

def format_report(results):
    """
    Formats the results for console output with checkmarks and X marks.
    """
    for result in results:
        doc = result["document"]
        present = result["present_keywords"]
        missing = result["missing_keywords"]
        print(f"{doc['filename']} ({doc['type']}):")
        if present:
            print("  ✓ Present:", ", ".join(present))
        if missing:
            print("  ✗ Missing:", ", ".join(missing))

# Example usage (for testing)
if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    # Use the loader function if present, else fallback to old code
    try:
        from checklist_validator import load_normalized_docs_and_checklist
        docs, checklist = load_normalized_docs_and_checklist()
    except ImportError:
        with open("outputs/normalized_docs.json", "r", encoding="utf-8") as f:
            docs = json.load(f)
        with open("config/checklist.yaml", "r", encoding="utf-8") as f:
            checklist = yaml.safe_load(f)["audit_completeness_checklist"]

    # Build a mapping from checklist id to required keywords
    checklist_map = {item["id"]: item["required_keywords"] for item in checklist}
    # Define mapping from normalized doc 'type' to checklist 'id'
    type_to_checklist_id = {
        "pdf": "invoices",
        "excel": "project_data",
        "word": "audit_rfi",
    }

    results = scan_and_report_keywords(docs, checklist_map, type_to_checklist_id)
    format_report(results)
