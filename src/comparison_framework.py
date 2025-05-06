"""
Comparison Framework Module
Compares static checklist-based compliance verification with dynamic policy-based approach.
Generates metrics, visualizations, and analysis of differences between approaches.

This module provides tools to:
1. Run both static and dynamic evaluations on the same document set
2. Calculate precision, recall, F1 score, and other comparative metrics
3. Generate visualizations and detailed reports on the differences
4. Provide recommendations on which approach is better for different scenarios
"""

import json
import yaml
import logging
import time
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict

# Optional imports
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Optional visualization support
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from matplotlib.patches import Patch
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
from typing import Dict, List, Tuple, Optional, Any, Union, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict

# Import both evaluation approaches
from .compliance_evaluator import ComplianceEvaluator, ComplianceLevel, DocumentComplianceReport
from .requirement_store import RequirementStore
from .policy_requirement_manager import PolicyRequirementManager

# For static evaluation
def static_evaluate_document(document: Dict, checklist_map: Dict, type_to_checklist_id: Dict) -> Dict:
    """
    Evaluates a document using the static checklist approach.
    
    Args:
        document: Dictionary containing document information
        checklist_map: Dictionary mapping checklist IDs to required keywords
        type_to_checklist_id: Dictionary mapping document types to checklist IDs
        
    Returns:
        Dictionary with evaluation results
    """
    doc_type = document.get("type", "")
    checklist_id = type_to_checklist_id.get(doc_type)
    
    if not checklist_id or checklist_id not in checklist_map:
        return {
            "document_id": document.get("filename", "unknown"),
            "status": "unknown_type",
            "missing": [],
            "present": [],
            "compliance_level": "indeterminate"
        }
    
    required_keywords = checklist_map[checklist_id]
    content = document.get("content", "").lower()
    
    present = [kw for kw in required_keywords if kw.lower() in content]
    missing = [kw for kw in required_keywords if kw.lower() not in content]
    
    # Determine compliance level based on static rules
    if not missing:
        compliance_level = "fully_compliant"
    elif len(present) >= len(required_keywords) / 2:
        compliance_level = "partially_compliant"
    else:
        compliance_level = "non_compliant"
    
    status = "complete" if not missing else "incomplete"
    
    return {
        "document_id": document.get("filename", "unknown"),
        "status": status,
        "missing": missing,
        "present": present,
        "compliance_level": compliance_level,
        "confidence_score": 1.0 if not missing else 0.5,
        "total_keywords": len(required_keywords),
        "matched_keywords": len(present),
        "missing_keywords": len(missing)
    }

def static_evaluate_documents(documents: List[Dict], checklist_path: str = "config/checklist.yaml") -> Dict[str, Dict]:
    """
    Evaluates multiple documents using the static checklist approach.
    
    Args:
        documents: List of document dictionaries
        checklist_path: Path to the checklist YAML file
        
    Returns:
        Dictionary mapping document IDs to evaluation results
    """
    # Load checklist
    with open(checklist_path, "r", encoding="utf-8") as f:
        checklist = yaml.safe_load(f)["audit_completeness_checklist"]
    
    # Build mappings
    type_to_checklist_id = {
        "pdf": "invoices",
        "excel": "project_data",
        "word": "audit_rfi",
        "text": "policy_requirements",
        "audit_rfi": "audit_rfi",
        "policy_requirements": "policy_requirements",
        "project_data": "project_data"
    }
    
    checklist_map = {item["id"]: item["required_keywords"] for item in checklist}
    
    # Evaluate each document
    start_time = time.time()
    results = {}
    for doc in documents:
        doc_id = doc.get("filename", "unknown")
        results[doc_id] = static_evaluate_document(doc, checklist_map, type_to_checklist_id)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Return results with performance metadata
    return {
        "results": results,
        "metadata": {
            "processing_time": processing_time,
            "documents_processed": len(documents),
            "method": "static",
            "timestamp": datetime.now().isoformat()
        }
    }

@dataclass
class ComparisonMetrics:
    """Metrics comparing static and dynamic approaches for a document"""
    document_id: str
    static_compliance: str  # fully_compliant, partially_compliant, non_compliant, indeterminate
    dynamic_compliance: str  # same as above
    static_confidence: float
    dynamic_confidence: float
    agreement: bool  # True if compliance levels match
    static_keywords_found: int
    dynamic_keywords_found: int
    static_justification: str = "None provided"
    dynamic_justification: str = "None provided"
    static_time: float = 0.0
    dynamic_time: float = 0.0
    static_metadata: Dict = field(default_factory=dict)
    dynamic_metadata: Dict = field(default_factory=dict)
    comparison_notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)

@dataclass
class BenchmarkDataset:
    """Benchmark dataset with ground truth compliance statuses"""
    documents: List[Dict]
    ground_truth: Dict[str, str]  # document_id -> compliance_level
    name: str
    description: str
    metadata: Dict = field(default_factory=dict)
    
    @classmethod
    def create_synthetic(cls, num_documents: int = 10, seed: int = 42) -> 'BenchmarkDataset':
        """Create a synthetic benchmark dataset with known compliance statuses"""
        import random
        random.seed(seed)
        
        compliance_levels = ["fully_compliant", "partially_compliant", "non_compliant"]
        document_types = ["audit_rfi", "policy_requirements", "project_data"]
        
        documents = []
        ground_truth = {}
        
        for i in range(num_documents):
            doc_id = f"synthetic_doc_{i+1}.pdf"
            doc_type = random.choice(document_types)
            compliance = random.choice(compliance_levels)
            
            # Generate content based on compliance level
            if compliance == "fully_compliant":
                # Include all keywords for the doc type
                content = f"This is a {doc_type} document. It includes all required keywords: "
                if doc_type == "audit_rfi":
                    content += "questionnaire response form compliance audit assessment controls review."
                elif doc_type == "policy_requirements":
                    content += "policy requirements mandatory regulation compliance rules security."
                else:  # project_data
                    content += "project timeline budget resources deliverables milestones data."
            
            elif compliance == "partially_compliant":
                # Include some keywords
                content = f"This is a {doc_type} document. It includes some keywords: "
                if doc_type == "audit_rfi":
                    content += "questionnaire response form."
                elif doc_type == "policy_requirements":
                    content += "policy requirements."
                else:  # project_data
                    content += "project timeline."
            
            else:  # non_compliant
                # Include no relevant keywords
                content = f"This document has no relevant keywords for {doc_type}."
            
            documents.append({
                "filename": doc_id,
                "type": doc_type,
                "content": content
            })
            
            ground_truth[doc_id] = compliance
        
        return cls(
            documents=documents,
            ground_truth=ground_truth,
            name=f"Synthetic Benchmark ({num_documents} docs)",
            description="Synthetic benchmark dataset with known compliance statuses",
            metadata={"seed": seed, "created": datetime.now().isoformat()}
        )
    
    def save(self, output_dir: Union[str, Path]) -> None:
        """Save the benchmark dataset to disk"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save documents
        docs_path = output_dir / "benchmark_documents.json"
        with open(docs_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
        
        # Save ground truth
        truth_path = output_dir / "benchmark_ground_truth.json"
        with open(truth_path, "w", encoding="utf-8") as f:
            json.dump(self.ground_truth, f, ensure_ascii=False, indent=2)
        
        # Save metadata
        meta_path = output_dir / "benchmark_metadata.json"
        meta = {
            "name": self.name,
            "description": self.description,
            "document_count": len(self.documents),
            "created": datetime.now().isoformat(),
            **self.metadata
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, input_dir: Union[str, Path]) -> 'BenchmarkDataset':
        """Load a benchmark dataset from disk"""
        input_dir = Path(input_dir)
        
        # Load documents
        docs_path = input_dir / "benchmark_documents.json"
        with open(docs_path, "r", encoding="utf-8") as f:
            documents = json.load(f)
        
        # Load ground truth
        truth_path = input_dir / "benchmark_ground_truth.json"
        with open(truth_path, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)
        
        # Load metadata
        meta_path = input_dir / "benchmark_metadata.json"
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        return cls(
            documents=documents,
            ground_truth=ground_truth,
            name=meta.get("name", "Loaded Benchmark"),
            description=meta.get("description", ""),
            metadata={k: v for k, v in meta.items() if k not in ["name", "description"]}
        )


class ComparisonFramework:
    """
    Framework for comparing static and dynamic compliance evaluation approaches.
    Provides methods to run both evaluations, calculate metrics, and generate reports.
    """
    
    def __init__(
        self,
        checklist_path: str = "config/checklist.yaml",
        requirement_store_path: Optional[str] = None,
        output_dir: str = "outputs/comparison"
    ):
        """
        Initialize the comparison framework.
        
        Args:
            checklist_path: Path to the static checklist YAML file
            requirement_store_path: Path to stored requirements for dynamic evaluation
            output_dir: Directory to save comparison results
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Static evaluation setup
        self.checklist_path = checklist_path
        
        # Dynamic evaluation setup
        self.requirement_store = RequirementStore(
            yaml_path=requirement_store_path or "config/policy_requirements.yaml"
        )
        self.requirement_manager = PolicyRequirementManager(store=self.requirement_store)
        self.dynamic_evaluator = ComplianceEvaluator(
            requirement_manager=self.requirement_manager,
            semantic_evaluation=True  # Use semantic evaluation by default
        )
    
    def compare_document(self, document: Dict) -> ComparisonMetrics:
        """
        Compare static and dynamic evaluation approaches on a single document.
        
        Args:
            document: Dictionary containing document information
            
        Returns:
            ComparisonMetrics with results from both approaches
        """
        # Properly load checklist with context manager
        with open(self.checklist_path, "r", encoding="utf-8") as f:
            checklist_data = yaml.safe_load(f)

        # Perform static evaluation
        static_start = time.time()
        static_result = static_evaluate_document(
            document,
            {item["id"]: item["required_keywords"] for item in checklist_data["audit_completeness_checklist"]},
            {
                "pdf": "invoices",
                "excel": "project_data",
                "word": "audit_rfi",
                "text": "policy_requirements",
                "audit_rfi": "audit_rfi",
                "policy_requirements": "policy_requirements",
                "project_data": "project_data"
            }
        )
        static_time = time.time() - static_start
        
        # Perform dynamic evaluation
        dynamic_start = time.time()
        dynamic_report = self.dynamic_evaluator.evaluate_document(document)
        dynamic_time = time.time() - dynamic_start
        
        # Extract metrics for comparison
        static_compliance = static_result["compliance_level"]
        dynamic_compliance = dynamic_report.overall_compliance.value
        
        # Create comparison metrics
        metrics = ComparisonMetrics(
            document_id=document.get("filename", "unknown"),
            static_compliance=static_compliance,
            dynamic_compliance=dynamic_compliance,
            static_confidence=static_result.get("confidence_score", 0.0),
            dynamic_confidence=dynamic_report.confidence_score,
            agreement=(static_compliance == dynamic_compliance),
            static_keywords_found=static_result.get("matched_keywords", 0),
            dynamic_keywords_found=sum(len(r.matched_keywords) for r in dynamic_report.results),
            static_justification=f"Found {static_result.get('matched_keywords', 0)} of {static_result.get('total_keywords', 0)} keywords",
            dynamic_justification=dynamic_report.summary,
            static_time=static_time,
            dynamic_time=dynamic_time,
            static_metadata=static_result,
            dynamic_metadata=asdict(dynamic_report)
        )
        
        # Add comparison notes
        if metrics.agreement:
            metrics.comparison_notes = f"Both approaches agree on {dynamic_compliance} status."
        else:
            metrics.comparison_notes = (
                f"Disagreement: Static reports {static_compliance} while dynamic reports {dynamic_compliance}. "
                f"Static confidence: {metrics.static_confidence:.2f}, Dynamic confidence: {metrics.dynamic_confidence:.2f}."
            )
        
        return metrics
    
    def compare_documents(self, documents: List[Dict]) -> Dict:
        """
        Compare static and dynamic evaluation approaches on multiple documents.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Dictionary with comparison results and metrics
        """
        self.logger.info(f"Starting comparison of {len(documents)} documents")
        
        results = []
        static_time_total = 0
        dynamic_time_total = 0
        
        for doc in documents:
            metrics = self.compare_document(doc)
            results.append(metrics.to_dict())
            static_time_total += metrics.static_time
            dynamic_time_total += metrics.dynamic_time
        
        # Calculate overall metrics
        total_docs = len(documents)
        agreements = sum(1 for r in results if r["agreement"])
        agreement_rate = agreements / total_docs if total_docs > 0 else 0
        
        # Count compliance levels
        static_levels = {
            "fully_compliant": sum(1 for r in results if r["static_compliance"] == "fully_compliant"),
            "partially_compliant": sum(1 for r in results if r["static_compliance"] == "partially_compliant"),
            "non_compliant": sum(1 for r in results if r["static_compliance"] == "non_compliant"),
            "indeterminate": sum(1 for r in results if r["static_compliance"] == "indeterminate")
        }
        
        dynamic_levels = {
            "fully_compliant": sum(1 for r in results if r["dynamic_compliance"] == "fully_compliant"),
            "partially_compliant": sum(1 for r in results if r["dynamic_compliance"] == "partially_compliant"),
            "non_compliant": sum(1 for r in results if r["dynamic_compliance"] == "non_compliant"),
            "not_applicable": sum(1 for r in results if r["dynamic_compliance"] == "not_applicable"),
            "indeterminate": sum(1 for r in results if r["dynamic_compliance"] == "indeterminate")
        }
        
        # Performance metrics
        performance = {
            "static_avg_time": static_time_total / total_docs if total_docs > 0 else 0,
            "dynamic_avg_time": dynamic_time_total / total_docs if total_docs > 0 else 0,
            "static_total_time": static_time_total,
            "dynamic_total_time": dynamic_time_total,
            "speed_ratio": static_time_total / dynamic_time_total if dynamic_time_total > 0 else float('inf')
        }
        
        return {
            "document_results": results,
            "summary": {
                "total_documents": total_docs,
                "agreements": agreements,
                "agreement_rate": agreement_rate,
                "static_compliance_counts": static_levels,
                "dynamic_compliance_counts": dynamic_levels,
                "performance": performance
            },
            "metadata": {
                "comparison_time": datetime.now().isoformat(),
                "static_checklist": self.checklist_path,
                "dynamic_requirements": self.requirement_store.yaml_path
            }
        }
    
    def calculate_benchmark_metrics(self, benchmark: BenchmarkDataset, comparison_results: Dict) -> Dict:
        """
        Calculate precision, recall, F1 score and other metrics against benchmark ground truth.
        
        Args:
            benchmark: BenchmarkDataset with ground truth
            comparison_results: Results from compare_documents
            
        Returns:
            Dictionary with precision, recall, F1 score for both approaches
        """
        document_results = comparison_results["document_results"]
        
        # Initialize confusion matrices for both approaches
        # Format: (TP, FP, TN, FN) for each compliance level
        compliance_levels = ["fully_compliant", "partially_compliant", "non_compliant"]
        static_confusion = {level: [0, 0, 0, 0] for level in compliance_levels}
        dynamic_confusion = {level: [0, 0, 0, 0] for level in compliance_levels}
        
        for result in document_results:
            doc_id = result["document_id"]
            
            # Skip if no ground truth
            if doc_id not in benchmark.ground_truth:
                continue
            
            truth = benchmark.ground_truth[doc_id]
            static_pred = result["static_compliance"]
            dynamic_pred = result["dynamic_compliance"]
            
            # Update confusion matrices for each level
            for level in compliance_levels:
                # Static approach metrics
                if static_pred == level and truth == level:
                    static_confusion[level][0] += 1  # TP
                elif static_pred == level and truth != level:
                    static_confusion[level][1] += 1  # FP
                elif static_pred != level and truth != level:
                    static_confusion[level][2] += 1  # TN
                elif static_pred != level and truth == level:
                    static_confusion[level][3] += 1  # FN
                
                # Dynamic approach metrics
                if dynamic_pred == level and truth == level:
                    dynamic_confusion[level][0] += 1  # TP
                elif dynamic_pred == level and truth != level:
                    dynamic_confusion[level][1] += 1  # FP
                elif dynamic_pred != level and truth != level:
                    dynamic_confusion[level][2] += 1  # TN
                elif dynamic_pred != level and truth == level:
                    dynamic_confusion[level][3] += 1  # FN
        
        # Calculate metrics for each approach and level
        static_metrics = {}
        dynamic_metrics = {}
        
        for level in compliance_levels:
            # Static metrics
            tp, fp, tn, fn = static_confusion[level]
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
            
            static_metrics[level] = {
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "accuracy": accuracy,
                "confusion_matrix": {
                    "true_positive": tp,
                    "false_positive": fp,
                    "true_negative": tn,
                    "false_negative": fn
                }
            }
            
            # Dynamic metrics
            tp, fp, tn, fn = dynamic_confusion[level]
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
            
            dynamic_metrics[level] = {
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "accuracy": accuracy,
                "confusion_matrix": {
                    "true_positive": tp,
                    "false_positive": fp,
                    "true_negative": tn,
                    "false_negative": fn
                }
            }
        
        # Overall metrics
        static_overall = self._calculate_overall_metrics(static_metrics)
        dynamic_overall = self._calculate_overall_metrics(dynamic_metrics)
        
        return {
            "static": {
                "by_level": static_metrics,
                "overall": static_overall
            },
            "dynamic": {
                "by_level": dynamic_metrics,
                "overall": dynamic_overall
            },
            "comparison": {
                "precision_diff": dynamic_overall["precision"] - static_overall["precision"],
                "recall_diff": dynamic_overall["recall"] - static_overall["recall"],
                "f1_diff": dynamic_overall["f1_score"] - static_overall["f1_score"],
                "accuracy_diff": dynamic_overall["accuracy"] - static_overall["accuracy"],
                "speed_ratio": comparison_results["summary"]["performance"]["speed_ratio"]
            }
        }
    
    def _calculate_overall_metrics(self, metrics_by_level: Dict) -> Dict:
        """Calculate overall metrics across all compliance levels"""
        total_precision = 0
        total_recall = 0
        total_f1 = 0
        total_accuracy = 0
        
        for level_metrics in metrics_by_level.values():
            total_precision += level_metrics["precision"]
            total_recall += level_metrics["recall"]
            total_f1 += level_metrics["f1_score"]
            total_accuracy += level_metrics["accuracy"]
        
        num_levels = len(metrics_by_level)
        if num_levels > 0:
            return {
                "precision": total_precision / num_levels,
                "recall": total_recall / num_levels,
                "f1_score": total_f1 / num_levels,
                "accuracy": total_accuracy / num_levels
            }
        else:
            return {
                "precision": 0,
                "recall": 0,
                "f1_score": 0,
                "accuracy": 0
            }
    
    def save_comparison_results(self, results: Dict, output_path: Optional[str] = None) -> str:
        """
        Save comparison results to a JSON file.
        
        Args:
            results: Comparison results dictionary
            output_path: Path to save the results (if None, a default path is generated)
            
        Returns:
            Path to the saved file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"comparison_results_{timestamp}.json"
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved comparison results to {output_path}")
        return str(output_path)
    
    def generate_html_report(self, results: Dict, output_path: Optional[str] = None) -> str:
        """
        Generate a user-friendly HTML report from comparison results.
        
        Args:
            results: Comparison results dictionary
            output_path: Path to save the HTML report (if None, a default path is generated)
            
        Returns:
            Path to the saved HTML report
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"comparison_report_{timestamp}.html"
        else:
            output_path = Path(output_path)
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create HTML content
        html_content = self._generate_html_content(results)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        self.logger.info(f"Generated HTML report at {output_path}")
        return str(output_path)
    
    def _generate_html_content(self, results: Dict) -> str:
        """Generate HTML content from comparison results"""
        # Basic HTML template with double braces to escape them from the formatter
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Compliance Approach Comparison Report</title>
            <style>
                body{{font-family:Arial,sans-serif;margin:20px;}}
                .container{{max-width:1200px;margin:0 auto;}}
                h1,h2,h3{{color:#333;}}
                .summary-box{{
                    background-color:#f5f5f5;
                    padding:15px;
                    margin:15px 0;
                    border-radius:5px;
                    border-left:5px solid #2c3e50;
                }}
                .metrics-table{{
                    width:100%;
                    border-collapse:collapse;
                    margin:15px 0;
                }}
                .metrics-table th,.metrics-table td{{
                    border:1px solid #ddd;
                    padding:8px;
                    text-align:left;
                }}
                .metrics-table th{{
                    background-color:#f2f2f2;
                }}
                .highlight{{
                    background-color:#e8f4f8;
                }}
                .agreement{{
                    color:green;
                    font-weight:bold;
                }}
                .disagreement{{
                    color:red;
                }}
                .chart-container{{
                    width:100%;
                    margin:20px 0;
                }}
                .better{{color:green;font-weight:bold;}}
                .worse{{color:red;}}
                .recommendations{{
                    background-color:#e8f4f8;
                    padding:15px;
                    margin:15px 0;
                    border-radius:5px;
                    border-left:5px solid #3498db;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Compliance Approach Comparison Report</h1>
                <p>This report compares the static checklist-based approach with the dynamic policy-based approach for compliance evaluation.</p>
                
                <div class="summary-box">
                    <h2>Summary</h2>
                    {summary_html}
                </div>
                
                <h2>Performance Comparison</h2>
                {performance_html}
                
                {metrics_html}
                
                <h2>Document Results</h2>
                {documents_html}
                
                <div class="recommendations">
                    <h2>Recommendations</h2>
                    {recommendations_html}
                </div>
            </div>
        </body>
        </html>
        """
        
        # Generate summary section
        summary = results.get("summary", {})
        summary_html = f"""
        <p><strong>Total Documents:</strong> {summary.get('total_documents', 0)}</p>
        <p><strong>Agreement Rate:</strong> {summary.get('agreement_rate', 0):.2%} ({summary.get('agreements', 0)} agreements)</p>
        <p><strong>Speed Comparison:</strong> Static is {summary.get('performance', {}).get('speed_ratio', 0):.2f}x faster than Dynamic</p>
        """
        
        # Generate performance comparison
        performance = summary.get("performance", {})
        performance_html = f"""
        <table class="metrics-table">
            <tr>
                <th>Metric</th>
                <th>Static Approach</th>
                <th>Dynamic Approach</th>
                <th>Difference</th>
            </tr>
            <tr>
                <td>Average Processing Time</td>
                <td>{performance.get('static_avg_time', 0):.4f} seconds</td>
                <td>{performance.get('dynamic_avg_time', 0):.4f} seconds</td>
                <td>{performance.get('static_avg_time', 0) - performance.get('dynamic_avg_time', 0):.4f} seconds</td>
            </tr>
            <tr>
                <td>Total Processing Time</td>
                <td>{performance.get('static_total_time', 0):.4f} seconds</td>
                <td>{performance.get('dynamic_total_time', 0):.4f} seconds</td>
                <td>{performance.get('static_total_time', 0) - performance.get('dynamic_total_time', 0):.4f} seconds</td>
            </tr>
        </table>
        """
        
        # Generate metrics comparison if available
        metrics_html = ""
        if "benchmark_metrics" in results:
            metrics = results["benchmark_metrics"]
            static_overall = metrics.get("static", {}).get("overall", {})
            dynamic_overall = metrics.get("dynamic", {}).get("overall", {})
            comparison = metrics.get("comparison", {})
            
            metrics_html = f"""
            <h2>Benchmark Metrics</h2>
            <table class="metrics-table">
                <tr>
                    <th>Metric</th>
                    <th>Static Approach</th>
                    <th>Dynamic Approach</th>
                    <th>Difference</th>
                </tr>
                <tr>
                    <td>Precision</td>
                    <td>{static_overall.get('precision', 0):.4f}</td>
                    <td>{dynamic_overall.get('precision', 0):.4f}</td>
                    <td class="{'better' if comparison.get('precision_diff', 0) > 0 else 'worse'}">{comparison.get('precision_diff', 0):.4f}</td>
                </tr>
                <tr>
                    <td>Recall</td>
                    <td>{static_overall.get('recall', 0):.4f}</td>
                    <td>{dynamic_overall.get('recall', 0):.4f}</td>
                    <td class="{'better' if comparison.get('recall_diff', 0) > 0 else 'worse'}">{comparison.get('recall_diff', 0):.4f}</td>
                </tr>
                <tr>
                    <td>F1 Score</td>
                    <td>{static_overall.get('f1_score', 0):.4f}</td>
                    <td>{dynamic_overall.get('f1_score', 0):.4f}</td>
                    <td class="{'better' if comparison.get('f1_diff', 0) > 0 else 'worse'}">{comparison.get('f1_diff', 0):.4f}</td>
                </tr>
                <tr>
                    <td>Accuracy</td>
                    <td>{static_overall.get('accuracy', 0):.4f}</td>
                    <td>{dynamic_overall.get('accuracy', 0):.4f}</td>
                    <td class="{'better' if comparison.get('accuracy_diff', 0) > 0 else 'worse'}">{comparison.get('accuracy_diff', 0):.4f}</td>
                </tr>
            </table>
            """
        
        # Generate document results
        documents_html = "<table class='metrics-table'>"
        documents_html += """
        <tr>
            <th>Document</th>
            <th>Static Compliance</th>
            <th>Dynamic Compliance</th>
            <th>Agreement</th>
            <th>Static Keywords</th>
            <th>Dynamic Keywords</th>
            <th>Processing Time</th>
            <th>Notes</th>
        </tr>
        """
        
        for doc in results.get("document_results", []):
            agreement_class = "agreement" if doc.get("agreement", False) else "disagreement"
            agreement_text = "✓" if doc.get("agreement", False) else "✗"
            
            documents_html += f"""
            <tr>
                <td>{doc.get('document_id', '')}</td>
                <td>{doc.get('static_compliance', '')}</td>
                <td>{doc.get('dynamic_compliance', '')}</td>
                <td class="{agreement_class}">{agreement_text}</td>
                <td>{doc.get('static_keywords_found', 0)}</td>
                <td>{doc.get('dynamic_keywords_found', 0)}</td>
                <td>S: {doc.get('static_time', 0):.3f}s, D: {doc.get('dynamic_time', 0):.3f}s</td>
                <td>{doc.get('comparison_notes', '')}</td>
            </tr>
            """
        
        documents_html += "</table>"
        
        # Generate recommendations
        has_metrics = "benchmark_metrics" in results
        performance = summary.get("performance", {})
        speed_ratio = performance.get("speed_ratio", 1)
        
        # Determine which method is more accurate (if metrics available)
        if has_metrics:
            metrics = results["benchmark_metrics"]
            dynamic_f1 = metrics.get("dynamic", {}).get("overall", {}).get("f1_score", 0)
            static_f1 = metrics.get("static", {}).get("overall", {}).get("f1_score", 0)
            
            dynamic_more_accurate = dynamic_f1 > static_f1
            accuracy_diff = abs(dynamic_f1 - static_f1)
            significant_diff = accuracy_diff > 0.1
        else:
            dynamic_more_accurate = None
            significant_diff = None
        
        # Generate recommendations based on results
        recommendations = []
        
        # Speed-based recommendations
        if speed_ratio > 5:
            recommendations.append(
                "The static approach is significantly faster than the dynamic approach. "
                "Consider using static checks for initial screening or time-sensitive applications."
            )
        
        # Accuracy-based recommendations (if metrics available)
        if has_metrics and dynamic_more_accurate and significant_diff:
            recommendations.append(
                "The dynamic approach achieves significantly higher accuracy than the static approach. "
                "Consider using dynamic evaluation for critical compliance checks where accuracy is paramount."
            )
        elif has_metrics and not dynamic_more_accurate and significant_diff:
            recommendations.append(
                "The static approach achieves comparable or better accuracy than the dynamic approach. "
                "Consider using static evaluation for most use cases due to its performance advantage."
            )
        elif has_metrics and not significant_diff:
            recommendations.append(
                "Both approaches achieve similar accuracy levels. "
                "Consider using static evaluation for routine checks, and reserve dynamic evaluation "
                "for complex or ambiguous documents that require deeper analysis."
            )
        
        # Agreement-based recommendations
        agreement_rate = summary.get("agreement_rate", 0)
        if agreement_rate < 0.5:
            recommendations.append(
                "The approaches show significant disagreement. Consider using both methods in parallel "
                "and manually reviewing cases where they disagree to establish best practices."
            )
        elif agreement_rate > 0.8:
            recommendations.append(
                "The approaches show strong agreement. Consider using the faster static approach "
                "for most cases, and only fall back to dynamic evaluation for edge cases."
            )
        
        # Format recommendations
        if recommendations:
            recommendations_html = "<ul>"
            for rec in recommendations:
                recommendations_html += f"<li>{rec}</li>"
            recommendations_html += "</ul>"
        else:
            recommendations_html = "<p>Insufficient data to provide specific recommendations.</p>"
        
        # Fill template
        # Use a raw string with {{}} for literal braces to avoid format conflicts with CSS properties
        html_template = html_template.replace("{font-family", "{{font-family")
        html_template = html_template.replace("{max-width", "{{max-width")
        html_template = html_template.replace("{color", "{{color")
        html_template = html_template.replace("{background-color", "{{background-color")
        html_template = html_template.replace("{padding", "{{padding")
        html_template = html_template.replace("{margin", "{{margin")
        html_template = html_template.replace("{border-radius", "{{border-radius")
        html_template = html_template.replace("{border-left", "{{border-left")
        html_template = html_template.replace("{width", "{{width")
        html_template = html_template.replace("{border-collapse", "{{border-collapse")
        html_template = html_template.replace("{text-align", "{{text-align")
        html_template = html_template.replace("{border", "{{border")
        
        try:
            html_content = html_template.format(
                summary_html=summary_html,
                performance_html=performance_html,
                metrics_html=metrics_html,
                documents_html=documents_html,
                recommendations_html=recommendations_html
            )
        except KeyError as e:
            self.logger.warning(f"Error formatting HTML template: {e}. Using simplified template.")
            # Fallback to simplified template
            simplified_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Compliance Approach Comparison Report</title>
            </head>
            <body>
                <h1>Compliance Approach Comparison Report</h1>
                <h2>Summary</h2>
                {summary_html}
                
                <h2>Performance Comparison</h2>
                {performance_html}
                
                {metrics_html}
                
                <h2>Document Results</h2>
                {documents_html}
                
                <h2>Recommendations</h2>
                {recommendations_html}
            </body>
            </html>
            """
            html_content = simplified_template.format(
                summary_html=summary_html,
                performance_html=performance_html,
                metrics_html=metrics_html,
                documents_html=documents_html,
                recommendations_html=recommendations_html
            )
        
        return html_content
    
    def generate_visualizations(self, results: Dict, output_dir: Optional[str] = None) -> List[str]:
        """
        Generate visualizations from comparison results.
        
        Args:
            results: Comparison results dictionary
            output_dir: Directory to save visualizations (if None, default output_dir is used)
            
        Returns:
            List of paths to generated visualization files
        """
        if output_dir is None:
            output_dir = self.output_dir / "visualizations"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize plots
        try:
            import matplotlib.pyplot as plt
            import matplotlib.colors as mcolors
            import numpy as np
            from matplotlib.patches import Patch
        except ImportError:
            self.logger.warning("Matplotlib not available. Skipping visualizations.")
            return []
        
        output_files = []
        
        # Plot 1: Compliance level distribution
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Static compliance levels
            static_levels = results.get("summary", {}).get("static_compliance_counts", {})
            static_labels = list(static_levels.keys())
            static_values = list(static_levels.values())
            
            # Dynamic compliance levels
            dynamic_levels = results.get("summary", {}).get("dynamic_compliance_counts", {})
            dynamic_labels = list(dynamic_levels.keys())
            dynamic_values = list(dynamic_levels.values())
            
            # Plot static
            ax1.pie(static_values, labels=static_labels, autopct='%1.1f%%',
                    shadow=True, startangle=90)
            ax1.set_title('Static Approach: Compliance Distribution')
            
            # Plot dynamic
            ax2.pie(dynamic_values, labels=dynamic_labels, autopct='%1.1f%%',
                    shadow=True, startangle=90)
            ax2.set_title('Dynamic Approach: Compliance Distribution')
            
            plt.tight_layout()
            
            # Save figure
            fig_path = output_dir / f"compliance_distribution_{timestamp}.png"
            plt.savefig(fig_path)
            output_files.append(str(fig_path))
            plt.close(fig)
            
        except Exception as e:
            self.logger.error(f"Error generating compliance distribution chart: {str(e)}")
        
        # Plot 2: Agreement analysis
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Count agreement types
            doc_results = results.get("document_results", [])
            agreement_counts = {"agreement": 0}
            disagreement_counts = {}
            
            for doc in doc_results:
                if doc.get("agreement", False):
                    agreement_counts["agreement"] += 1
                else:
                    # Track specific disagreement types
                    static = doc.get("static_compliance", "")
                    dynamic = doc.get("dynamic_compliance", "")
                    pair = f"{static} → {dynamic}"
                    
                    if pair not in disagreement_counts:
                        disagreement_counts[pair] = 0
                    disagreement_counts[pair] += 1
            
            # Combine data
            labels = list(agreement_counts.keys()) + list(disagreement_counts.keys())
            values = list(agreement_counts.values()) + list(disagreement_counts.values())
            
            # Colors
            agreement_colors = ['green']
            disagreement_colors = [plt.cm.Reds(i/len(disagreement_counts)) 
                                  for i in range(len(disagreement_counts))]
            colors = agreement_colors + list(disagreement_colors)
            
            # Plot
            ax.bar(range(len(labels)), values, color=colors)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha="right")
            ax.set_title('Agreement Analysis')
            ax.set_ylabel('Number of Documents')
            
            plt.tight_layout()
            
            # Save figure
            fig_path = output_dir / f"agreement_analysis_{timestamp}.png"
            plt.savefig(fig_path)
            output_files.append(str(fig_path))
            plt.close(fig)
            
        except Exception as e:
            self.logger.error(f"Error generating agreement analysis chart: {str(e)}")
        
        # Plot 3: Performance comparison
        try:
            if "benchmark_metrics" in results:
                metrics = results.get("benchmark_metrics", {})
                static_metrics = metrics.get("static", {}).get("overall", {})
                dynamic_metrics = metrics.get("dynamic", {}).get("overall", {})
                
                # Extract metrics
                metric_names = ['Precision', 'Recall', 'F1 Score', 'Accuracy']
                static_values = [
                    static_metrics.get("precision", 0),
                    static_metrics.get("recall", 0),
                    static_metrics.get("f1_score", 0),
                    static_metrics.get("accuracy", 0)
                ]
                dynamic_values = [
                    dynamic_metrics.get("precision", 0),
                    dynamic_metrics.get("recall", 0),
                    dynamic_metrics.get("f1_score", 0),
                    dynamic_metrics.get("accuracy", 0)
                ]
                
                # Set up the figure
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # Set position of bars on X axis
                x = np.arange(len(metric_names))
                width = 0.35
                
                # Make the plot
                rects1 = ax.bar(x - width/2, static_values, width, label='Static')
                rects2 = ax.bar(x + width/2, dynamic_values, width, label='Dynamic')
                
                # Add labels, title and legend
                ax.set_ylabel('Score')
                ax.set_title('Performance Metrics Comparison')
                ax.set_xticks(x)
                ax.set_xticklabels(metric_names)
                ax.set_ylim(0, 1.0)
                ax.legend()
                
                # Add value labels
                def autolabel(rects):
                    for rect in rects:
                        height = rect.get_height()
                        ax.annotate(f'{height:.2f}',
                                   xy=(rect.get_x() + rect.get_width()/2, height),
                                   xytext=(0, 3),
                                   textcoords="offset points",
                                   ha='center', va='bottom')
                
                autolabel(rects1)
                autolabel(rects2)
                
                plt.tight_layout()
                
                # Save figure
                fig_path = output_dir / f"performance_metrics_{timestamp}.png"
                plt.savefig(fig_path)
                output_files.append(str(fig_path))
                plt.close(fig)
        except Exception as e:
            self.logger.error(f"Error generating performance metrics chart: {str(e)}")
        
        return output_files
    
    def run_benchmark_comparison(self, benchmark: BenchmarkDataset) -> Dict:
        """
        Run a complete benchmark comparison and generate all outputs.
        
        Args:
            benchmark: BenchmarkDataset to use for comparison
            
        Returns:
            Dictionary with complete comparison results including metrics and paths to outputs
        """
        self.logger.info(f"Starting benchmark comparison with {len(benchmark.documents)} documents")
        
        # Run comparison on benchmark documents
        comparison_results = self.compare_documents(benchmark.documents)
        
        # Calculate metrics against ground truth
        benchmark_metrics = self.calculate_benchmark_metrics(benchmark, comparison_results)
        comparison_results["benchmark_metrics"] = benchmark_metrics
        
        # Generate outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_prefix = f"benchmark_{benchmark.name.replace(' ', '_')}_{timestamp}"
        
        json_path = self.save_comparison_results(
            comparison_results, 
            self.output_dir / f"{output_prefix}.json"
        )
        
        html_path = self.generate_html_report(
            comparison_results,
            self.output_dir / f"{output_prefix}.html"
        )
        
        viz_paths = self.generate_visualizations(
            comparison_results,
            self.output_dir / "visualizations"
        )
        
        # Add output paths to results
        comparison_results["outputs"] = {
            "json_report": json_path,
            "html_report": html_path,
            "visualizations": viz_paths
        }
        
        return comparison_results


# Demo function
def run_sample_comparison():
    """Run a sample comparison using synthetic benchmark data"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Creating synthetic benchmark dataset")
    benchmark = BenchmarkDataset.create_synthetic(num_documents=15, seed=42)
    
    logger.info("Initializing comparison framework")
    framework = ComparisonFramework(
        checklist_path="config/checklist.yaml",
        output_dir="outputs/comparison"
    )
    
    logger.info("Running benchmark comparison")
    results = framework.run_benchmark_comparison(benchmark)
    
    logger.info(f"Comparison completed. Results saved to {results['outputs']['html_report']}")
    
    # Print some key metrics
    if "benchmark_metrics" in results:
        metrics = results["benchmark_metrics"]
        static_f1 = metrics["static"]["overall"]["f1_score"]
        dynamic_f1 = metrics["dynamic"]["overall"]["f1_score"]
        speed_ratio = results["summary"]["performance"]["speed_ratio"]
        
        logger.info(f"Static F1 Score: {static_f1:.4f}")
        logger.info(f"Dynamic F1 Score: {dynamic_f1:.4f}")
        logger.info(f"Speed Ratio: Static is {speed_ratio:.2f}x faster than Dynamic")
        
        if dynamic_f1 > static_f1:
            logger.info(f"Dynamic approach is more accurate by {dynamic_f1 - static_f1:.4f} F1 points")
        else:
            logger.info(f"Static approach is more accurate by {static_f1 - dynamic_f1:.4f} F1 points")
    
    return results


if __name__ == "__main__":
    run_sample_comparison()