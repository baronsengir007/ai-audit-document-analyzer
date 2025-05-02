import json
import yaml
from pathlib import Path
import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
import time
from concurrent.futures import ThreadPoolExecutor
import argparse

from document_processor import (
    extract_text_from_pdf,
    extract_text_from_word,
    extract_text_from_excel
)
from document_classifier import classify_document
from checklist_validator import scan_and_report_keywords

@dataclass
class ValidationConfig:
    """Configuration for the validation process"""
    strict_mode: bool = False
    batch_size: int = 5
    max_workers: int = 4
    log_level: str = "INFO"
    output_format: str = "json"  # json, csv, or console
    detailed_report: bool = True
    test_dir: Optional[Path] = None  # For testing purposes

class ValidationLoop:
    """Main validation loop for processing documents against checklists"""
    
    def __init__(self, config: ValidationConfig):
        self.config = config
        self.setup_logging()
        self.checklist_map = self._load_checklist()
        self.type_to_checklist_id = {
            "invoice": "invoices",
            "audit_rfi": "audit_rfi",
            "project_data": "project_data",
            "checklist": "checklist",
            "policy_requirements": "policy_requirements",
            "unknown": "unknown"
        }

    def setup_logging(self):
        """Configure logging based on config"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler("validation.log"),
                logging.StreamHandler()
            ]
        )

    def _load_checklist(self) -> Dict[str, List[str]]:
        """Load checklist from YAML file"""
        try:
            checklist_path = "config/checklist.yaml"
            if self.config.test_dir:
                checklist_path = Path(self.config.test_dir) / "config" / "checklist.yaml"
            with open(checklist_path, "r", encoding="utf-8") as f:
                checklist = yaml.safe_load(f)["audit_completeness_checklist"]
            return {item["id"]: item["required_keywords"] for item in checklist}
        except Exception as e:
            logging.error(f"Failed to load checklist: {e}")
            raise

    def process_document(self, doc_path: Path) -> Dict[str, Any]:
        """Process a single document through the validation pipeline"""
        try:
            # Extract text based on file type
            if doc_path.suffix.lower() == '.pdf':
                content = extract_text_from_pdf(str(doc_path))
            elif doc_path.suffix.lower() == '.docx':
                content = extract_text_from_word(str(doc_path))
            elif doc_path.suffix.lower() == '.xlsx':
                content = extract_text_from_excel(str(doc_path))
            else:
                raise ValueError(f"Unsupported file type: {doc_path.suffix}")

            # Create document object
            doc = {
                "filename": doc_path.name,
                "type": doc_path.suffix.lower()[1:],  # Remove dot
                "content": content
            }

            # Classify document
            classification = classify_document(doc)
            doc["classification"] = classification

            # Validate against checklist
            checklist_id = self.type_to_checklist_id.get(classification)
            if not checklist_id:
                logging.warning(f"No checklist mapping for document type: {classification}")
                return {
                    "document": doc,
                    "status": "unknown_type",
                    "validation_results": None
                }

            # Scan for keywords
            results = scan_and_report_keywords(
                [doc],
                self.checklist_map,
                self.type_to_checklist_id
            )

            if not results:  # No results means document was skipped
                return {
                    "document": doc,
                    "status": "unknown_type",
                    "validation_results": None
                }

            result = results[0]  # Get first (and only) result
            status = "complete" if not result["missing_keywords"] else "incomplete"
            if self.config.strict_mode and result["missing_keywords"]:
                status = "incomplete"

            return {
                "document": doc,
                "status": status,
                "validation_results": result
            }

        except Exception as e:
            logging.error(f"Error processing document {doc_path}: {e}")
            return {
                "document": {"filename": doc_path.name},
                "status": "error",
                "error": str(e)
            }

    def process_batch(self, doc_paths: List[Path]) -> List[Dict[str, Any]]:
        """Process a batch of documents in parallel"""
        results = []
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = [executor.submit(self.process_document, path) for path in doc_paths]
            for future in futures:
                results.append(future.result())
        return results

    def validate_documents(self, input_dir: Union[str, Path]) -> Dict[str, Any]:
        """Main validation loop that processes all documents in the input directory"""
        input_dir = Path(input_dir)
        if not input_dir.exists():
            raise ValueError(f"Input directory does not exist: {input_dir}")

        # Get all document files
        doc_paths = []
        for ext in ['.pdf', '.docx', '.xlsx']:
            doc_paths.extend(input_dir.glob(f"*{ext}"))

        if not doc_paths:
            logging.warning(f"No documents found in {input_dir}")
            return {"status": "no_documents", "results": []}

        # Process documents in batches
        all_results = []
        for i in range(0, len(doc_paths), self.config.batch_size):
            batch = doc_paths[i:i + self.config.batch_size]
            logging.info(f"Processing batch {i//self.config.batch_size + 1}")
            batch_results = self.process_batch(batch)
            all_results.extend(batch_results)

        # Generate summary
        summary = {
            "total_documents": len(doc_paths),
            "processed_documents": len(all_results),
            "complete_documents": sum(1 for r in all_results if r["status"] == "complete"),
            "incomplete_documents": sum(1 for r in all_results if r["status"] == "incomplete"),
            "error_documents": sum(1 for r in all_results if r["status"] == "error"),
            "unknown_type_documents": sum(1 for r in all_results if r["status"] == "unknown_type")
        }

        return {
            "status": "success",
            "summary": summary,
            "results": all_results
        }

    def save_results(self, results: Dict[str, Any], output_path: Optional[Path] = None):
        """Save validation results in the configured format"""
        if not output_path:
            output_path = Path("outputs/validation_results.json")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.config.output_format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        elif self.config.output_format == "console":
            self._print_results(results)
        else:
            raise ValueError(f"Unsupported output format: {self.config.output_format}")

    def _print_results(self, results: Dict[str, Any]):
        """Print results to console in a readable format"""
        print("\n=== Validation Results Summary ===")
        print(f"Total Documents: {results['summary']['total_documents']}")
        print(f"Complete: {results['summary']['complete_documents']}")
        print(f"Incomplete: {results['summary']['incomplete_documents']}")
        print(f"Errors: {results['summary']['error_documents']}")
        print(f"Unknown Type: {results['summary']['unknown_type_documents']}")

        if self.config.detailed_report:
            print("\n=== Detailed Results ===")
            for result in results["results"]:
                print(f"\nDocument: {result['document']['filename']}")
                print(f"Status: {result['status']}")
                if result["status"] == "error":
                    print(f"Error: {result['error']}")
                elif result["validation_results"]:
                    vr = result["validation_results"]
                    if vr["missing_keywords"]:
                        print("Missing Keywords:", ", ".join(vr["missing_keywords"]))
                    if vr["present_keywords"]:
                        print("Present Keywords:", ", ".join(vr["present_keywords"]))

def main():
    """Command line interface for the validation loop"""
    parser = argparse.ArgumentParser(description="Document Validation System")
    parser.add_argument("input_dir", help="Directory containing documents to validate")
    parser.add_argument("--strict", action="store_true", help="Enable strict validation mode")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of documents to process in parallel")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum number of worker threads")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    parser.add_argument("--output-format", choices=["json", "console"], default="json")
    parser.add_argument("--output-file", help="Path to save results (for json format)")
    parser.add_argument("--detailed", action="store_true", help="Include detailed results in output")

    args = parser.parse_args()

    config = ValidationConfig(
        strict_mode=args.strict,
        batch_size=args.batch_size,
        max_workers=args.max_workers,
        log_level=args.log_level,
        output_format=args.output_format,
        detailed_report=args.detailed
    )

    try:
        validator = ValidationLoop(config)
        results = validator.validate_documents(args.input_dir)
        
        if args.output_file:
            validator.save_results(results, Path(args.output_file))
        else:
            validator.save_results(results)
            
    except Exception as e:
        logging.error(f"Validation failed: {e}")
        raise

if __name__ == "__main__":
    main() 