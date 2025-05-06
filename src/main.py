"""
Main application entry point for AI Audit Document Scanner
Implements end-to-end workflow for both static and dynamic compliance modes.
"""

import argparse
import logging
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .document_loader import load_and_normalize_documents
from .document_classifier import classify_document
from .policy_parser import PolicyParser
from .policy_requirement_manager import PolicyRequirementManager
from .requirement_store import RequirementStore
from .compliance_evaluator import ComplianceEvaluator, DocumentComplianceReport, ComplianceLevel
from .llm_wrapper import OllamaWrapper
from .unified_workflow_manager import UnifiedWorkflowManager


def setup_logging(log_level=logging.INFO):
    """Configure logging with appropriate formatting"""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("audit_scanner.log")
        ]
    )
    return logging.getLogger(__name__)


class AuditDocumentScanner:
    """
    Main application class that orchestrates the complete workflow
    for audit document scanning and compliance evaluation.
    """
    
    def __init__(
            self,
            input_dir: Path = Path("docs"),
            output_dir: Path = Path("outputs"),
            config_dir: Path = Path("config"),
            use_semantic_evaluation: bool = True,
            llm_model: str = "mistral",
            workflow_mode: str = "unified"  # New parameter for workflow mode
    ):
        """
        Initialize the audit document scanner
        
        Args:
            input_dir: Directory containing input documents
            output_dir: Directory for output reports
            config_dir: Directory for configuration files
            use_semantic_evaluation: Whether to use semantic LLM evaluation
            llm_model: LLM model to use
            workflow_mode: Mode of operation (unified, static, or dynamic)
        """
        self.logger = logging.getLogger(__name__)
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config_dir = config_dir
        self.workflow_mode = workflow_mode
        
        # Ensure directories exist
        self.output_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # Set up paths
        self.normalized_docs_path = self.output_dir / "normalized_docs.json"
        self.requirements_path = self.config_dir / "policy_requirements.yaml"
        self.compliance_matrix_path = self.output_dir / "compliance_matrix.json"
        self.workflow_config_path = self.config_dir / "workflow_config.yaml"
        
        # Initialize components
        self.llm = OllamaWrapper(model=llm_model)
        self.policy_parser = PolicyParser(llm=self.llm)
        self.requirement_store = RequirementStore(yaml_path=self.requirements_path)
        self.requirement_manager = PolicyRequirementManager(
            yaml_path=self.requirements_path,
            parser=self.policy_parser,
            store=self.requirement_store
        )
        self.compliance_evaluator = ComplianceEvaluator(
            requirement_manager=self.requirement_manager,
            llm=self.llm,
            semantic_evaluation=use_semantic_evaluation
        )
        
        # Initialize unified workflow manager
        self.workflow_manager = UnifiedWorkflowManager(config_path=self.workflow_config_path)
        
        self.documents = []
        self.classified_docs = {}
        
    def load_documents(self) -> List[Dict]:
        """
        Load and normalize documents from the input directory
        
        Returns:
            List of normalized document dictionaries
        """
        self.logger.info(f"Loading documents from {self.input_dir}")
        
        if self.normalized_docs_path.exists():
            self.logger.info(f"Loading cached normalized documents from {self.normalized_docs_path}")
            try:
                with open(self.normalized_docs_path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                self.logger.info(f"Loaded {len(self.documents)} documents from cache")
                return self.documents
            except Exception as e:
                self.logger.warning(f"Error loading cached documents: {e}. Will load from source.")
        
        self.documents = load_and_normalize_documents(self.input_dir)
        self.logger.info(f"Loaded {len(self.documents)} documents from {self.input_dir}")
        
        # Save normalized documents
        with open(self.normalized_docs_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Saved normalized documents to {self.normalized_docs_path}")
        
        return self.documents
    
    def classify_documents(self) -> Dict[str, List[Dict]]:
        """
        Classify loaded documents by type
        
        Returns:
            Dictionary mapping document types to lists of documents
        """
        self.logger.info("Classifying documents by type")
        
        self.classified_docs = {}
        for doc in self.documents:
            # Add classification if not already present
            if 'classified_type' not in doc:
                doc['classified_type'] = classify_document(doc)
            
            doc_type = doc['classified_type']
            if doc_type not in self.classified_docs:
                self.classified_docs[doc_type] = []
            self.classified_docs[doc_type].append(doc)
        
        # Log classification results
        for doc_type, docs in self.classified_docs.items():
            self.logger.info(f"Found {len(docs)} documents of type '{doc_type}'")
        
        return self.classified_docs
    
    def extract_requirements(self) -> int:
        """
        Extract requirements from policy documents
        
        Returns:
            Number of requirements extracted
        """
        self.logger.info("Extracting requirements from policy documents")
        
        # Get policy documents
        policy_docs = self.classified_docs.get('policy_requirements', [])
        if not policy_docs:
            self.logger.warning("No policy documents found for requirement extraction")
            return 0
        
        # Clear existing requirements if needed
        existing_reqs = self.requirement_manager.get_all_requirements()
        if existing_reqs:
            self.logger.info(f"Found {len(existing_reqs)} existing requirements")
            
            # Check if we should extract again
            if not policy_docs and existing_reqs:
                self.logger.info("Using existing requirements")
                return len(existing_reqs)
        else:
            self.logger.info("No existing requirements found, will extract from policy documents")
        
        # Extract requirements from each policy document
        total_extracted = 0
        for doc in policy_docs:
            self.logger.info(f"Processing policy document: {doc['filename']}")
            try:
                # Create a temporary file with the document content
                temp_file = self.output_dir / f"temp_{doc['filename']}"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(doc['content'])
                
                # Extract requirements
                result = self.requirement_manager.extract_and_store(
                    temp_file, 
                    auto_save=True
                )
                success_count = sum(1 for v in result.values() if v)
                self.logger.info(f"Extracted {success_count} requirements from {doc['filename']}")
                total_extracted += success_count
                
                # Clean up temp file
                temp_file.unlink()
                
            except Exception as e:
                self.logger.error(f"Error extracting requirements from {doc['filename']}: {e}")
        
        # Log results
        if total_extracted > 0:
            self.logger.info(f"Successfully extracted a total of {total_extracted} requirements")
            
            # Export to JSON for inspection
            json_path = self.output_dir / "requirements.json"
            self.requirement_manager.export_to_json(json_path)
            self.logger.info(f"Exported requirements to {json_path}")
        else:
            self.logger.warning("No requirements were extracted")
        
        return total_extracted
    
    def evaluate_compliance(self) -> Dict[str, DocumentComplianceReport]:
        """
        Evaluate audit documents against extracted requirements
        
        Returns:
            Dictionary mapping document IDs to compliance reports
        """
        self.logger.info("Evaluating document compliance against requirements")
        
        # Check if we have requirements
        requirements = self.requirement_manager.get_all_requirements()
        if not requirements:
            self.logger.error("No requirements available for compliance evaluation")
            return {}
        
        # Get audit documents
        audit_docs = []
        for doc_type, docs in self.classified_docs.items():
            # Include most document types except policy requirements (source)
            if doc_type != 'policy_requirements':
                audit_docs.extend(docs)
        
        if not audit_docs:
            self.logger.warning("No audit documents found for compliance evaluation")
            return {}
        
        # Evaluate compliance based on workflow mode
        self.logger.info(f"Evaluating {len(audit_docs)} documents using {self.workflow_mode} mode")
        compliance_reports = {}
        
        for doc in audit_docs:
            try:
                if self.workflow_mode == "unified":
                    result = self.workflow_manager.process_document(doc)
                elif self.workflow_mode == "static":
                    result = self.workflow_manager.process_document(doc, mode="static")
                elif self.workflow_mode == "dynamic":
                    result = self.workflow_manager.process_document(doc, mode="dynamic")
                else:
                    raise ValueError(f"Invalid workflow mode: {self.workflow_mode}")
                
                # Convert result to DocumentComplianceReport
                report = DocumentComplianceReport(
                    document_id=doc['filename'],
                    document_type=doc.get('type', 'unknown'),
                    document_name=doc['filename'],
                    overall_compliance=ComplianceLevel.FULLY_COMPLIANT if result.is_compliant else ComplianceLevel.NON_COMPLIANT,
                    confidence_score=result.confidence,
                    summary=f"Compliance assessment using {result.mode_used if hasattr(result, 'mode_used') else self.workflow_mode} mode",
                    metadata={
                        "details": result.details if hasattr(result, 'details') else {},
                        "mode_used": result.mode_used if hasattr(result, 'mode_used') else self.workflow_mode
                    }
                )
                compliance_reports[doc['filename']] = report
                
            except Exception as e:
                self.logger.error(f"Error evaluating compliance for {doc['filename']}: {e}")
        
        # Save individual reports
        reports_dir = self.output_dir / "compliance_reports"
        reports_dir.mkdir(exist_ok=True)
        
        for doc_id, report in compliance_reports.items():
            report_path = reports_dir / f"{doc_id.replace('.', '_')}_compliance.json"
            self.compliance_evaluator.save_document_report(report, report_path)
            self.logger.info(f"Saved compliance report for {doc_id} to {report_path}")
        
        return compliance_reports
    
    def run_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete audit document scanning pipeline
        
        Returns:
            Dictionary with summary results
        """
        start_time = datetime.now()
        self.logger.info(f"Starting audit document scanning pipeline at {start_time}")
        
        # Step 1: Load and normalize documents
        self.load_documents()
        
        # Step 2: Classify documents
        self.classify_documents()
        
        # Step 3: Extract requirements from policy documents
        requirements_count = self.extract_requirements()
        
        # Step 4: Evaluate compliance
        compliance_reports = self.evaluate_compliance()
        
        # Generate summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "documents_processed": len(self.documents),
            "requirements_extracted": requirements_count,
            "documents_evaluated": len(compliance_reports),
            "fully_compliant": sum(1 for r in compliance_reports.values() 
                                  if r.overall_compliance.value == 'fully_compliant'),
            "partially_compliant": sum(1 for r in compliance_reports.values() 
                                      if r.overall_compliance.value == 'partially_compliant'),
            "non_compliant": sum(1 for r in compliance_reports.values() 
                                if r.overall_compliance.value == 'non_compliant')
        }
        
        # Save summary
        summary_path = self.output_dir / "pipeline_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Completed audit document scanning pipeline in {duration:.2f} seconds")
        self.logger.info(f"Summary: {len(self.documents)} documents processed, "
                        f"{requirements_count} requirements extracted, "
                        f"{len(compliance_reports)} documents evaluated")
        
        return summary


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="AI Audit Document Scanner")
    parser.add_argument("--input-dir", type=Path, default=Path("docs"),
                        help="Directory containing input documents")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"),
                        help="Directory for output reports")
    parser.add_argument("--config-dir", type=Path, default=Path("config"),
                        help="Directory for configuration files")
    parser.add_argument("--llm-model", type=str, default="mistral",
                        help="LLM model to use for analysis")
    parser.add_argument("--workflow-mode", type=str, default="unified",
                        choices=["unified", "static", "dynamic"],
                        help="Workflow mode to use (unified, static, or dynamic)")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    logger = setup_logging(getattr(logging, args.log_level))
    
    try:
        scanner = AuditDocumentScanner(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            config_dir=args.config_dir,
            llm_model=args.llm_model,
            workflow_mode=args.workflow_mode
        )
        
        results = scanner.run_pipeline()
        logger.info("Pipeline completed successfully")
        
        # Print summary
        print("\nSummary:")
        print(f"Documents processed: {len(results.get('documents', []))}")
        print(f"Requirements extracted: {len(results.get('requirements', []))}")
        print(f"Compliance reports generated: {len(results.get('compliance_reports', {}))}")
        
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()