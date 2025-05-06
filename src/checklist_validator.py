import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def load_normalized_docs() -> List[Dict[str, Any]]:
    """Load normalized documents from JSON file"""
    try:
        with open("outputs/normalized_docs.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("normalized_docs.json not found, returning empty list")
        return []
    except Exception as e:
        logger.error(f"Error loading normalized_docs.json: {e}")
        return []

def scan_and_report_keywords(documents: List[Dict[str, Any]], 
                           checklist_map: Dict[str, List[str]], 
                           type_to_checklist_id: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Scan documents for keywords and report findings
    
    Args:
        documents: List of document dictionaries with content and classification
        checklist_map: Dictionary mapping checklist IDs to keyword lists
        type_to_checklist_id: Dictionary mapping document types to checklist IDs
        
    Returns:
        List of dictionaries with scan results
    """
    results = []
    
    for doc in documents:
        try:
            content = doc["content"].lower()
            doc_type = doc["classification"]
            
            # Get checklist ID for document type
            checklist_id = type_to_checklist_id.get(doc_type)
            if not checklist_id:
                logger.warning(f"No checklist found for document type: {doc_type}")
                continue
                
            # Get keywords for checklist
            keywords = checklist_map.get(checklist_id, [])
            if not keywords:
                logger.warning(f"No keywords found for checklist: {checklist_id}")
                continue
                
            # Scan for keywords
            present_keywords = []
            missing_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in content:
                    present_keywords.append(keyword)
                else:
                    missing_keywords.append(keyword)
                    
            # Create result
            result = {
                "document_type": doc_type,
                "checklist_id": checklist_id,
                "present_keywords": present_keywords,
                "missing_keywords": missing_keywords,
                "total_keywords": len(keywords),
                "found_keywords": len(present_keywords)
            }
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error scanning document: {e}")
            continue
            
    return results

def save_scan_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> None:
    """Save scan results to JSON file"""
    if not output_path:
        output_path = Path("outputs/scan_results.json")
        
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving scan results: {e}")

def get_compliance_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary of compliance results"""
    total_docs = len(results)
    fully_compliant = sum(1 for r in results if not r["missing_keywords"])
    partially_compliant = sum(1 for r in results if r["missing_keywords"] and r["present_keywords"])
    non_compliant = sum(1 for r in results if not r["present_keywords"])
    
    return {
        "total_documents": total_docs,
        "fully_compliant": fully_compliant,
        "partially_compliant": partially_compliant,
        "non_compliant": non_compliant,
        "compliance_rate": fully_compliant / total_docs if total_docs > 0 else 0
    }
