"""
Results Visualizer Module
Generates HTML and JSON reports for document classification results.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

class ResultsVisualizer:
    """
    Generates visual reports for document classification and verification results.
    Supports HTML and JSON output formats with professional styling.
    """
    
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize the results visualizer.
        
        Args:
            output_dir: Directory to save generated reports
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir)
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        
        # Track generated reports
        self.generated_reports = []
    
    def generate_report(
        self,
        verification_result: Dict[str, Any],
        classified_documents: List[Dict[str, Any]] = None,
        format: str = "html",
        filename: str = None
    ) -> str:
        """
        Generate a report in the specified format.
        
        Args:
            verification_result: Result from TypeVerification.verify_documents()
            classified_documents: Optional list of classified documents for detailed reports
            format: Report format ("html" or "json")
            filename: Optional filename for the report (without extension)
            
        Returns:
            Path to the generated report file
        """
        # Generate default filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"classification_report_{timestamp}"
        
        # Add appropriate extension
        file_extension = format.lower()
        output_file = self.output_dir / f"{filename}.{file_extension}"
        
        # Generate report in specified format
        if format.lower() == "html":
            content = self._generate_html_report(verification_result, classified_documents)
        elif format.lower() == "json":
            content = self._generate_json_report(verification_result, classified_documents)
        else:
            self.logger.error(f"Unsupported report format: {format}")
            return None
        
        # Write report to file
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.logger.info(f"Generated {format.upper()} report: {output_file}")
            self.generated_reports.append(str(output_file))
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Error writing report to {output_file}: {e}")
            return None
    
    def _generate_json_report(
        self,
        verification_result: Dict[str, Any],
        classified_documents: List[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a JSON report from verification results.
        
        Args:
            verification_result: Result from TypeVerification.verify_documents()
            classified_documents: Optional list of classified documents for detailed reporting
            
        Returns:
            JSON report as a string
        """
        # Create base report structure
        report = {
            "report_type": "document_classification",
            "timestamp": datetime.now().isoformat(),
            "verification_result": verification_result
        }
        
        # Add detailed document results if provided
        if classified_documents:
            # Create a simplified view of the documents by type
            documents_by_type = {}
            for doc in classified_documents:
                if "classification_result" not in doc:
                    continue
                    
                type_id = doc["classification_result"].get("type_id", "unknown")
                if type_id not in documents_by_type:
                    documents_by_type[type_id] = []
                
                documents_by_type[type_id].append({
                    "filename": doc.get("filename", "unknown"),
                    "confidence": doc["classification_result"].get("confidence", 0),
                    "rationale": doc["classification_result"].get("rationale", ""),
                    "evidence": doc["classification_result"].get("evidence", [])
                })
            
            report["documents_by_type"] = documents_by_type
        
        # Add summary stats
        report["summary"] = {
            "total_documents": verification_result.get("total_documents", 0),
            "total_required_types": verification_result.get("total_required_types", 0),
            "total_found_required_types": verification_result.get("total_found_required_types", 0),
            "total_missing_types": verification_result.get("total_missing_types", 0),
            "coverage_percentage": round(verification_result.get("coverage", 0) * 100, 1),
            "confidence_threshold": verification_result.get("confidence_threshold", 0)
        }
        
        return json.dumps(report, indent=2)
    
    def _generate_html_report(
        self,
        verification_result: Dict[str, Any],
        classified_documents: List[Dict[str, Any]] = None
    ) -> str:
        """
        Generate an HTML report from verification results.
        
        Args:
            verification_result: Result from TypeVerification.verify_documents()
            classified_documents: Optional list of classified documents for detailed reporting
            
        Returns:
            HTML report as a string
        """
        # Define HTML style and structure
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Document Classification Report</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1, h2, h3 {
                    color: #2c3e50;
                }
                h1 {
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }
                .summary-card {
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 20px;
                    margin-bottom: 30px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .dashboard {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .metric-card {
                    background-color: white;
                    border-radius: 5px;
                    padding: 15px;
                    flex: 1;
                    min-width: 200px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    text-align: center;
                }
                .metric-value {
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #3498db;
                    margin-bottom: 5px;
                }
                .metric-name {
                    font-size: 0.9em;
                    color: #7f8c8d;
                    text-transform: uppercase;
                }
                .coverage-good {
                    color: #27ae60;
                }
                .coverage-warning {
                    color: #f39c12;
                }
                .coverage-bad {
                    color: #e74c3c;
                }
                .document-type {
                    background-color: white;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                .document-type h3 {
                    margin-top: 0;
                    display: flex;
                    justify-content: space-between;
                }
                .document-count {
                    background-color: #3498db;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 0.8em;
                }
                .missing {
                    border-left: 5px solid #e74c3c;
                }
                .found {
                    border-left: 5px solid #27ae60;
                }
                .extra {
                    border-left: 5px solid #f39c12;
                }
                .document-list {
                    margin-top: 15px;
                    overflow-x: auto;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                th {
                    background-color: #f2f2f2;
                }
                tr:hover {
                    background-color: #f5f5f5;
                }
                .confident {
                    color: #27ae60;
                    font-weight: bold;
                }
                .uncertain {
                    color: #e74c3c;
                }
                .timestamp {
                    color: #7f8c8d;
                    font-size: 0.9em;
                    text-align: right;
                    margin-top: 40px;
                }
                .evidence-list {
                    font-size: 0.9em;
                    color: #555;
                    margin-top: 5px;
                    padding-left: 20px;
                }
                .evidence-item {
                    font-style: italic;
                    margin-bottom: 3px;
                }
                .collapsible {
                    background-color: #f8f9fa;
                    cursor: pointer;
                    padding: 10px;
                    width: 100%;
                    border: none;
                    text-align: left;
                    outline: none;
                    border-radius: 5px;
                }
                .active, .collapsible:hover {
                    background-color: #e9ecef;
                }
                .content {
                    padding: 0 18px;
                    max-height: 0;
                    overflow: hidden;
                    transition: max-height 0.2s ease-out;
                    background-color: white;
                }
            </style>
        </head>
        <body>
            <h1>Document Classification Report</h1>
            
            <!-- Summary Dashboard -->
            <div class="summary-card">
                <h2>Summary</h2>
                <div class="dashboard">
                    <div class="metric-card">
                        <div class="metric-value">{total_documents}</div>
                        <div class="metric-name">Documents</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{total_found_required}/{total_required}</div>
                        <div class="metric-name">Required Types Found</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value {coverage_class}">{coverage_percentage}%</div>
                        <div class="metric-name">Coverage</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{total_missing}</div>
                        <div class="metric-name">Missing Types</div>
                    </div>
                </div>
                <p>Confidence threshold: {confidence_threshold}</p>
            </div>
            
            <!-- Document Types Sections -->
            <h2>Document Types Overview</h2>
            
            <!-- Found Types -->
            <h3>Found Required Document Types</h3>
            {found_types_html}
            
            <!-- Missing Types -->
            <h3>Missing Required Document Types</h3>
            {missing_types_html}
            
            <!-- Extra Types -->
            <h3>Additional Document Types</h3>
            {extra_types_html}
            
            <!-- Unclassified Documents -->
            <h3>Unclassified Documents</h3>
            {unclassified_documents_html}
            
            <!-- Document Details Section -->
            {document_details_html}
            
            <!-- Timestamp -->
            <div class="timestamp">Report generated on {timestamp}</div>
            
            <script>
            var coll = document.getElementsByClassName("collapsible");
            var i;

            for (i = 0; i < coll.length; i++) {
                coll[i].addEventListener("click", function() {
                    this.classList.toggle("active");
                    var content = this.nextElementSibling;
                    if (content.style.maxHeight) {
                        content.style.maxHeight = null;
                    } else {
                        content.style.maxHeight = content.scrollHeight + "px";
                    }
                });
            }
            </script>
        </body>
        </html>
        """
        
        # Determine coverage class for color coding
        coverage = verification_result.get("coverage", 0) * 100
        if coverage >= 90:
            coverage_class = "coverage-good"
        elif coverage >= 70:
            coverage_class = "coverage-warning"
        else:
            coverage_class = "coverage-bad"
            
        # Generate HTML for found types
        found_types_html = ""
        if verification_result.get("found_types"):
            for doc_type in verification_result["found_types"]:
                found_types_html += f"""
                <div class="document-type found">
                    <h3>{doc_type['name']} <span class="document-count">{doc_type.get('document_count', 0)} documents</span></h3>
                    <p>{doc_type['description']}</p>
                </div>
                """
        else:
            found_types_html = "<p>No required document types were found.</p>"
        
        # Generate HTML for missing types
        missing_types_html = ""
        if verification_result.get("missing_types"):
            for doc_type in verification_result["missing_types"]:
                missing_types_html += f"""
                <div class="document-type missing">
                    <h3>{doc_type['name']}</h3>
                    <p>{doc_type['description']}</p>
                </div>
                """
        else:
            missing_types_html = "<p>All required document types are present.</p>"
        
        # Generate HTML for extra types
        extra_types_html = ""
        if verification_result.get("extra_types"):
            for doc_type in verification_result["extra_types"]:
                extra_types_html += f"""
                <div class="document-type extra">
                    <h3>{doc_type['name']} <span class="document-count">{doc_type.get('document_count', 0)} documents</span></h3>
                    <p>{doc_type['description']}</p>
                </div>
                """
        else:
            extra_types_html = "<p>No additional document types were found.</p>"
        
        # Generate HTML for unclassified documents
        unclassified_documents_html = ""
        if verification_result.get("unclassified_documents"):
            unclassified_documents_html += "<ul>"
            for doc in verification_result["unclassified_documents"]:
                unclassified_documents_html += f"""
                <li>{doc['filename']} (confidence: {doc['confidence']:.2f})</li>
                """
            unclassified_documents_html += "</ul>"
        else:
            unclassified_documents_html = "<p>All documents were classified with confidence above threshold.</p>"
        
        # Generate detailed document HTML if documents are provided
        document_details_html = ""
        if classified_documents:
            document_details_html = """
            <h2>Detailed Document Classification</h2>
            <button class="collapsible">Show Document Details</button>
            <div class="content">
                <div class="document-list">
                    <table>
                        <tr>
                            <th>Filename</th>
                            <th>Type</th>
                            <th>Confidence</th>
                            <th>Rationale</th>
                            <th>Evidence</th>
                        </tr>
            """
            
            for doc in classified_documents:
                if "classification_result" not in doc:
                    continue
                
                classification = doc["classification_result"]
                confidence = classification.get("confidence", 0)
                confidence_class = "confident" if confidence >= verification_result.get("confidence_threshold", 0.7) else "uncertain"
                
                # Format evidence list
                evidence_html = ""
                evidence_items = classification.get("evidence", [])
                if evidence_items:
                    evidence_html = "<ul class='evidence-list'>"
                    for item in evidence_items[:3]:  # Limit to first 3 evidence items
                        evidence_html += f"<li class='evidence-item'>\"{item}\"</li>"
                    if len(evidence_items) > 3:
                        evidence_html += f"<li>... and {len(evidence_items) - 3} more</li>"
                    evidence_html += "</ul>"
                
                document_details_html += f"""
                <tr>
                    <td>{doc.get('filename', 'unknown')}</td>
                    <td>{classification.get('type_name', 'Unknown')}</td>
                    <td class="{confidence_class}">{confidence:.2f}</td>
                    <td>{classification.get('rationale', '')[:100]}...</td>
                    <td>{evidence_html}</td>
                </tr>
                """
            
            document_details_html += """
                    </table>
                </div>
            </div>
            """
        
        # Fill in template
        html_report = html_template.format(
            total_documents=verification_result.get("total_documents", 0),
            total_required=verification_result.get("total_required_types", 0),
            total_found_required=verification_result.get("total_found_required_types", 0),
            total_missing=verification_result.get("total_missing_types", 0),
            coverage_percentage=f"{coverage:.1f}",
            coverage_class=coverage_class,
            confidence_threshold=verification_result.get("confidence_threshold", 0.7),
            found_types_html=found_types_html,
            missing_types_html=missing_types_html,
            extra_types_html=extra_types_html,
            unclassified_documents_html=unclassified_documents_html,
            document_details_html=document_details_html,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return html_report
    
    def generate_all_reports(
        self,
        verification_result: Dict[str, Any],
        classified_documents: List[Dict[str, Any]] = None,
        base_filename: str = None
    ) -> Dict[str, str]:
        """
        Generate reports in all supported formats.
        
        Args:
            verification_result: Result from TypeVerification.verify_documents()
            classified_documents: Optional list of classified documents for detailed reports
            base_filename: Optional base filename for reports (without extension)
            
        Returns:
            Dictionary mapping format to report file path
        """
        if not base_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"classification_report_{timestamp}"
        
        report_paths = {}
        
        # Generate HTML report
        html_path = self.generate_report(
            verification_result,
            classified_documents,
            format="html",
            filename=base_filename
        )
        if html_path:
            report_paths["html"] = html_path
        
        # Generate JSON report
        json_path = self.generate_report(
            verification_result,
            classified_documents,
            format="json",
            filename=base_filename
        )
        if json_path:
            report_paths["json"] = json_path
        
        return report_paths


# Standalone function that uses the ResultsVisualizer class
def generate_visualization_reports(
    verification_result: Dict[str, Any],
    classified_documents: List[Dict[str, Any]] = None,
    output_dir: str = "outputs",
    formats: List[str] = ["html", "json"]
) -> Dict[str, str]:
    """
    Generate visualization reports for document classification results.
    
    Args:
        verification_result: Result from TypeVerification.verify_documents()
        classified_documents: Optional list of classified documents for detailed reports
        output_dir: Directory to save generated reports
        formats: List of formats to generate ("html", "json")
        
    Returns:
        Dictionary mapping format to report file path
    """
    visualizer = ResultsVisualizer(output_dir=output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"classification_report_{timestamp}"
    
    report_paths = {}
    for format in formats:
        path = visualizer.generate_report(
            verification_result,
            classified_documents,
            format=format,
            filename=base_filename
        )
        if path:
            report_paths[format] = path
    
    return report_paths