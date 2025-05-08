"""
Main application entry point for AI Document Classification System.
Orchestrates the full document classification pipeline:
load → classify → verify → report.
"""

import argparse
import logging
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import core components
from .document_processor import DocumentProcessor
from .semantic_classifier import SemanticClassifier
from .type_verification import TypeVerification
from .results_visualizer import ResultsVisualizer
from .llm_wrapper import OllamaWrapper


def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Configure logging with appropriate formatting.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=handlers
    )
    return logging.getLogger(__name__)


class DocumentClassificationSystem:
    """
    Main application class that orchestrates the document classification workflow.
    
    Implements the full pipeline:
    1. Load documents using DocumentProcessor
    2. Classify documents using SemanticClassifier
    3. Verify document types using TypeVerification
    4. Generate reports using ResultsVisualizer
    """
    
    def __init__(
            self,
            input_dir: Path = Path("docs"),
            output_dir: Path = Path("outputs"),
            config_dir: Path = Path("config"),
            llm_model: str = "mistral",
            confidence_threshold: float = 0.7,
            use_cache: bool = True
    ):
        """
        Initialize the document classification system.
        
        Args:
            input_dir: Directory containing input documents
            output_dir: Directory for output reports
            config_dir: Directory for configuration files
            llm_model: LLM model to use
            confidence_threshold: Minimum confidence threshold for classification
            use_cache: Whether to use cached results when available
        """
        self.logger = logging.getLogger(__name__)
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config_dir = config_dir
        self.confidence_threshold = confidence_threshold
        self.use_cache = use_cache
        
        # Ensure directories exist
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # Set up paths
        self.document_types_path = self.config_dir / "document_types.yaml"
        self.normalized_docs_path = self.output_dir / "normalized_docs.json"
        self.classification_results_path = self.output_dir / "classification_results.json"
        self.verification_results_path = self.output_dir / "verification_results.json"
        
        # Initialize components
        self.logger.info("Initializing document classification system components...")
        
        # Document processor for loading and extracting text
        self.document_processor = DocumentProcessor(logger=self.logger)
        
        # Semantic classifier for document classification
        self.semantic_classifier = SemanticClassifier(
            config_path=str(self.document_types_path),
            llm_model=llm_model,
            confidence_threshold=confidence_threshold
        )
        
        # Type verification for checking required document types
        self.type_verifier = TypeVerification(
            config_path=str(self.document_types_path),
            confidence_threshold=confidence_threshold
        )
        
        # Results visualizer for generating reports
        self.results_visualizer = ResultsVisualizer(output_dir=str(self.output_dir))
        
        # Storage for pipeline results
        self.documents = []
        self.classified_documents = []
        self.verification_result = {}
        self.report_paths = {}
    
    def process_documents(self) -> List[Dict[str, Any]]:
        """
        Process documents from the input directory.
        Loads, extracts text, and normalizes documents.
        
        Returns:
            List of processed document dictionaries
        """
        self.logger.info(f"Processing documents from {self.input_dir}")
        
        # Check for cached normalized documents
        if self.use_cache and self.normalized_docs_path.exists():
            self.logger.info(f"Loading cached normalized documents from {self.normalized_docs_path}")
            try:
                with open(self.normalized_docs_path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                self.logger.info(f"Loaded {len(self.documents)} documents from cache")
                return self.documents
            except Exception as e:
                self.logger.warning(f"Error loading cached documents: {e}. Will process from source.")
        
        # Process documents from input directory
        processed_documents = []
        
        # Find all document files
        document_paths = []
        for ext in ['.pdf', '.docx', '.xlsx']:
            document_paths.extend(list(self.input_dir.glob(f"**/*{ext}")))
        
        if not document_paths:
            self.logger.warning(f"No supported documents found in {self.input_dir}")
            return []
        
        self.logger.info(f"Found {len(document_paths)} documents to process")
        
        # Process each document
        for doc_path in document_paths:
            self.logger.info(f"Processing document: {doc_path.name}")
            try:
                # Process document to extract text and metadata
                document_obj = self.document_processor.process_document(doc_path)
                
                # Convert to dictionary format expected by other components
                document_dict = {
                    "filename": document_obj.filename,
                    "content": document_obj.content,
                    "metadata": document_obj.metadata,
                    "source_path": document_obj.source_path
                }
                
                processed_documents.append(document_dict)
                self.logger.debug(f"Successfully processed {doc_path.name}")
                
            except Exception as e:
                self.logger.error(f"Error processing {doc_path.name}: {e}")
        
        self.logger.info(f"Successfully processed {len(processed_documents)} documents")
        
        # Save normalized documents
        if processed_documents:
            with open(self.normalized_docs_path, 'w', encoding='utf-8') as f:
                json.dump(processed_documents, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved normalized documents to {self.normalized_docs_path}")
        
        self.documents = processed_documents
        return processed_documents
    
    def classify_documents(self) -> List[Dict[str, Any]]:
        """
        Classify documents using semantic classification.
        
        Returns:
            List of classified document dictionaries
        """
        self.logger.info("Classifying documents using semantic classifier")
        
        # Check for cached classification results
        if self.use_cache and self.classification_results_path.exists():
            self.logger.info(f"Loading cached classification results from {self.classification_results_path}")
            try:
                with open(self.classification_results_path, 'r', encoding='utf-8') as f:
                    self.classified_documents = json.load(f)
                self.logger.info(f"Loaded classification results for {len(self.classified_documents)} documents")
                return self.classified_documents
            except Exception as e:
                self.logger.warning(f"Error loading cached classification results: {e}. Will classify from scratch.")
        
        if not self.documents:
            self.logger.warning("No documents to classify")
            return []
        
        # Classify documents using semantic classifier
        self.classified_documents = self.semantic_classifier.batch_classify(self.documents)
        
        # Count documents by type
        type_counts = {}
        for doc in self.classified_documents:
            if 'classification_result' in doc:
                type_id = doc['classification_result'].get('type_id', 'unknown')
                type_name = doc['classification_result'].get('type_name', 'Unknown')
                key = f"{type_name} ({type_id})"
                
                if key not in type_counts:
                    type_counts[key] = 0
                type_counts[key] += 1
        
        # Log classification results
        self.logger.info(f"Classified {len(self.classified_documents)} documents")
        for type_name, count in type_counts.items():
            self.logger.info(f"  - {type_name}: {count} documents")
        
        # Save classification results
        with open(self.classification_results_path, 'w', encoding='utf-8') as f:
            json.dump(self.classified_documents, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Saved classification results to {self.classification_results_path}")
        
        return self.classified_documents
    
    def verify_document_types(self) -> Dict[str, Any]:
        """
        Verify document types against required types.
        
        Returns:
            Dictionary with verification results
        """
        self.logger.info("Verifying document types against requirements")
        
        # Check for cached verification results
        if self.use_cache and self.verification_results_path.exists():
            self.logger.info(f"Loading cached verification results from {self.verification_results_path}")
            try:
                with open(self.verification_results_path, 'r', encoding='utf-8') as f:
                    self.verification_result = json.load(f)
                self.logger.info("Loaded verification results from cache")
                return self.verification_result
            except Exception as e:
                self.logger.warning(f"Error loading cached verification results: {e}. Will verify from scratch.")
        
        if not self.classified_documents:
            self.logger.warning("No classified documents to verify")
            return {}
        
        # Verify document types
        self.verification_result = self.type_verifier.verify_documents(self.classified_documents)
        
        # Log verification results
        coverage = self.verification_result.get("coverage", 0) * 100
        found = self.verification_result.get("total_found_required_types", 0)
        required = self.verification_result.get("total_required_types", 0)
        missing = self.verification_result.get("total_missing_types", 0)
        
        self.logger.info(f"Verification complete: {found}/{required} required types found ({coverage:.1f}% coverage)")
        
        if missing > 0:
            self.logger.warning(f"Missing {missing} required document types:")
            for doc_type in self.verification_result.get("missing_types", []):
                self.logger.warning(f"  - {doc_type['name']}: {doc_type['description']}")
        
        # Save verification results
        with open(self.verification_results_path, 'w', encoding='utf-8') as f:
            json.dump(self.verification_result, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Saved verification results to {self.verification_results_path}")
        
        return self.verification_result
    
    def generate_reports(self, formats=["html", "json"]) -> Dict[str, str]:
        """
        Generate reports for verification results.
        
        Args:
            formats: List of report formats to generate
            
        Returns:
            Dictionary mapping format to report path
        """
        self.logger.info(f"Generating {', '.join(formats)} reports")
        
        if not self.verification_result:
            self.logger.warning("No verification results to generate reports for")
            return {}
        
        # Generate timestamp for report filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"classification_report_{timestamp}"
        
        # Generate reports for each format
        self.report_paths = {}
        for format in formats:
            try:
                path = self.results_visualizer.generate_report(
                    self.verification_result,
                    self.classified_documents,
                    format=format,
                    filename=base_filename
                )
                
                if path:
                    self.report_paths[format] = path
                    self.logger.info(f"Generated {format.upper()} report: {path}")
            except Exception as e:
                self.logger.error(f"Error generating {format} report: {e}")
        
        return self.report_paths
    
    def run_pipeline(self) -> Dict[str, Any]:
        """
        Run the full document classification pipeline.
        
        Steps:
        1. Process documents (load, extract, normalize)
        2. Classify documents (semantic classification)
        3. Verify document types (against required types)
        4. Generate reports (HTML and JSON)
        
        Returns:
            Dictionary with summary results
        """
        start_time = datetime.now()
        self.logger.info(f"Starting document classification pipeline at {start_time}")
        
        # Step 1: Process documents
        processing_start = time.time()
        self.process_documents()
        processing_time = time.time() - processing_start
        
        # Step 2: Classify documents
        classification_start = time.time()
        self.classify_documents()
        classification_time = time.time() - classification_start
        
        # Step 3: Verify document types
        verification_start = time.time()
        self.verify_document_types()
        verification_time = time.time() - verification_start
        
        # Step 4: Generate reports
        reporting_start = time.time()
        self.generate_reports(formats=["html", "json"])
        reporting_time = time.time() - reporting_start
        
        # Generate summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Create detailed performance metrics
        performance = {
            "document_processing_seconds": processing_time,
            "classification_seconds": classification_time,
            "verification_seconds": verification_time,
            "reporting_seconds": reporting_time
        }
        
        # Combine with verification results for a complete summary
        summary = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "documents_processed": len(self.documents),
            "documents_classified": len(self.classified_documents),
            "required_types_found": self.verification_result.get("total_found_required_types", 0),
            "required_types_missing": self.verification_result.get("total_missing_types", 0),
            "coverage_percentage": self.verification_result.get("coverage", 0) * 100,
            "performance_metrics": performance,
            "report_paths": self.report_paths
        }
        
        # Save summary
        summary_path = self.output_dir / "pipeline_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Completed document classification pipeline in {duration:.2f} seconds")
        self.logger.info(f"Summary: {len(self.documents)} documents processed, "
                       f"{summary['required_types_found']}/{summary['required_types_found'] + summary['required_types_missing']} "
                       f"required types found ({summary['coverage_percentage']:.1f}% coverage)")
        
        return summary


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Document Classification System")
    parser.add_argument("--input-dir", type=Path, default=Path("docs"),
                        help="Directory containing input documents")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"),
                        help="Directory for output reports")
    parser.add_argument("--config-dir", type=Path, default=Path("config"),
                        help="Directory for configuration files")
    parser.add_argument("--llm-model", type=str, default="mistral",
                        help="LLM model to use for classification")
    parser.add_argument("--confidence", type=float, default=0.7,
                        help="Confidence threshold for classification (0-1)")
    parser.add_argument("--no-cache", action="store_true",
                        help="Disable loading cached results")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    parser.add_argument("--log-file", type=str, default="document_classification.log",
                        help="Log file path")
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    logger = setup_logging(
        log_level=getattr(logging, args.log_level),
        log_file=args.log_file
    )
    
    try:
        # Initialize the classification system
        system = DocumentClassificationSystem(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            config_dir=args.config_dir,
            llm_model=args.llm_model,
            confidence_threshold=args.confidence,
            use_cache=not args.no_cache
        )
        
        # Run the pipeline
        results = system.run_pipeline()
        logger.info("Pipeline completed successfully")
        
        # Print summary
        print("\nDocument Classification Summary:")
        print(f"Documents processed: {results['documents_processed']}")
        print(f"Documents classified: {results['documents_classified']}")
        print(f"Required types found: {results['required_types_found']}/{results['required_types_found'] + results['required_types_missing']}")
        print(f"Coverage: {results['coverage_percentage']:.1f}%")
        print("\nPerformance:")
        print(f"Document processing: {results['performance_metrics']['document_processing_seconds']:.2f} seconds")
        print(f"Classification: {results['performance_metrics']['classification_seconds']:.2f} seconds")
        print(f"Verification: {results['performance_metrics']['verification_seconds']:.2f} seconds")
        print(f"Reporting: {results['performance_metrics']['reporting_seconds']:.2f} seconds")
        print(f"Total duration: {results['duration_seconds']:.2f} seconds")
        
        # Print report locations
        if results.get('report_paths'):
            print("\nReports:")
            for format, path in results['report_paths'].items():
                print(f" - {format.upper()}: {path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error running pipeline: {e}", exc_info=True)
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())