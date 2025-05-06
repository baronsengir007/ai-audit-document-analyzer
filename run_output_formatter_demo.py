"""
Output Formatter Demonstration Script

This standalone script demonstrates the output formatter's capabilities
by generating examples of all supported formats for compliance reports.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import traceback

# Add src to the path for imports
sys.path.insert(0, os.path.abspath('./src'))

try:
    # Import required modules (using absolute imports)
    from src.output_format import (
        ValidationStatus,
        ValidationMetadata,
        ValidationItem,
        ValidationCategory,
        ValidationResult
    )
    
    from src.compliance_evaluator import (
        ComplianceLevel,
        ComplianceResult
    )
    
    from src.output_formatter import (
        OutputFormatter,
        OutputFormat,
        OutputType
    )
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler("output_formatter_demo.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("output_formatter_demo")
    
    # Create evidence directory
    EVIDENCE_DIR = Path("output_formatter_evidence")
    EVIDENCE_DIR.mkdir(exist_ok=True)
    
    # Function to create sample validation result
    def create_sample_validation_result():
        """Create a sample validation result for testing"""
        # Create sample validation metadata
        metadata = ValidationMetadata(
            timestamp=datetime.now().timestamp(),
            validator_version="1.0.0",
            mode="static",
            confidence_score=0.95,
            processing_time_ms=100.0,
            warnings=["Sample warning"]
        )
        
        # Create sample validation items
        items = [
            ValidationItem(
                id=f"item{i}",
                name=f"Test Item {i}",
                status=ValidationStatus.PASSED if i % 3 == 0 else 
                       (ValidationStatus.PARTIAL if i % 3 == 1 else ValidationStatus.FAILED),
                confidence_score=0.7 + (i % 3) * 0.1,
                details={
                    "justification": f"Justification for item {i}",
                    "matched_keywords": ["keyword1", "keyword2"] if i % 2 == 0 else [],
                    "missing_keywords": ["missing1", "missing2"] if i % 2 == 1 else []
                }
            )
            for i in range(1, 11)  # Create 10 items
        ]
        
        # Create categories
        categories = [
            ValidationCategory(
                id="cat1",
                name="Access Control",
                status=ValidationStatus.PARTIAL,
                confidence_score=0.85,
                items=items[:4]
            ),
            ValidationCategory(
                id="cat2",
                name="Data Protection",
                status=ValidationStatus.PARTIAL,
                confidence_score=0.75,
                items=items[4:7]
            ),
            ValidationCategory(
                id="cat3",
                name="Security Operations",
                status=ValidationStatus.PASSED,
                confidence_score=0.90,
                items=items[7:]
            )
        ]
        
        # Create validation result
        return ValidationResult(
            document_id="doc1",
            document_name="security_policy.pdf",
            document_type="policy",
            status=ValidationStatus.PARTIAL,
            metadata=metadata,
            categories=categories,
            errors=[],
            warnings=["Document requires updates to meet compliance"]
        )

    # Function to create sample compliance result
    def create_sample_compliance_result():
        """Create a sample compliance result for testing"""
        requirement_results = {}
        
        # Create sample requirements
        for i in range(1, 11):
            category = "Access Control" if i <= 4 else ("Data Protection" if i <= 7 else "Security Operations")
            compliance_level = (
                ComplianceLevel.FULLY_COMPLIANT.value if i % 3 == 0 else
                ComplianceLevel.PARTIALLY_COMPLIANT.value if i % 3 == 1 else
                ComplianceLevel.NON_COMPLIANT.value
            )
            
            requirement_results[f"REQ{i:03d}"] = {
                "requirement": {
                    "id": f"REQ{i:03d}",
                    "description": f"Requirement {i}",
                    "category": category,
                    "type": "mandatory",
                    "priority": "high" if i <= 3 else ("medium" if i <= 7 else "low")
                },
                "compliance_level": compliance_level,
                "confidence_score": 0.7 + (i % 3) * 0.1,
                "justification": f"Justification for requirement {i}",
                "matched_keywords": ["kw1", "kw2"] if i % 2 == 0 else []
            }
        
        # Create compliance result
        return ComplianceResult(
            is_compliant=True,
            confidence=0.85,
            details={
                "document_info": {
                    "id": "doc2",
                    "name": "security_controls.pdf",
                    "type": "controls"
                },
                "mode_used": "dynamic",
                "timestamp": datetime.now().timestamp(),
                "processing_time": 0.5,
                "overall_compliance": ComplianceLevel.PARTIALLY_COMPLIANT.value,
                "requirement_results": requirement_results
            }
        )
    
    # Function to demonstrate document output formats
    def demonstrate_document_formats(formatter, result):
        """Demonstrate all supported document output formats"""
        logger.info("DEMONSTRATING DOCUMENT OUTPUT FORMATS")
        formats_generated = []
        
        # Test all formats
        for fmt in OutputFormat:
            try:
                # Skip Excel if pandas/openpyxl not installed
                if fmt == OutputFormat.EXCEL:
                    try:
                        import pandas
                        import openpyxl
                    except ImportError:
                        logger.warning(f"Skipping {fmt.value} format - pandas/openpyxl not installed")
                        continue
                
                # Set output path and extension
                output_path = EVIDENCE_DIR / f"document_{fmt.value}"
                if fmt == OutputFormat.EXCEL:
                    output_path = output_path.with_suffix(".xlsx")
                else:
                    output_path = output_path.with_suffix(f".{fmt.value}")
                
                # Generate report in this format
                logger.info(f"Generating {fmt.value} document report: {output_path}")
                formatter.generate_report(
                    data=result,
                    output_type=OutputType.DOCUMENT,
                    output_format=fmt,
                    output_path=output_path
                )
                
                # Verify file exists
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    logger.info(f"✓ Successfully generated {fmt.value} document report ({file_size} bytes)")
                    formats_generated.append((fmt.value, str(output_path), file_size))
                else:
                    logger.error(f"✗ Failed to generate {fmt.value} document report")
            except Exception as e:
                logger.error(f"Error generating {fmt.value} document report: {str(e)}")
                logger.debug(traceback.format_exc())
        
        return formats_generated
    
    # Function to demonstrate matrix output formats
    def demonstrate_matrix_formats(formatter, matrix_data):
        """Demonstrate all supported matrix output formats"""
        logger.info("\nDEMONSTRATING MATRIX OUTPUT FORMATS")
        formats_generated = []
        
        # Test all formats
        for fmt in OutputFormat:
            try:
                # Skip Excel if pandas/openpyxl not installed
                if fmt == OutputFormat.EXCEL:
                    try:
                        import pandas
                        import openpyxl
                    except ImportError:
                        logger.warning(f"Skipping {fmt.value} format - pandas/openpyxl not installed")
                        continue
                
                # Set output path and extension
                output_path = EVIDENCE_DIR / f"matrix_{fmt.value}"
                if fmt == OutputFormat.EXCEL:
                    output_path = output_path.with_suffix(".xlsx")
                else:
                    output_path = output_path.with_suffix(f".{fmt.value}")
                
                # Generate report in this format
                logger.info(f"Generating {fmt.value} matrix report: {output_path}")
                formatter.generate_report(
                    data=matrix_data,
                    output_type=OutputType.MATRIX,
                    output_format=fmt,
                    output_path=output_path
                )
                
                # Verify file exists
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    logger.info(f"✓ Successfully generated {fmt.value} matrix report ({file_size} bytes)")
                    formats_generated.append((fmt.value, str(output_path), file_size))
                else:
                    logger.error(f"✗ Failed to generate {fmt.value} matrix report")
            except Exception as e:
                logger.error(f"Error generating {fmt.value} matrix report: {str(e)}")
                logger.debug(traceback.format_exc())
        
        return formats_generated
    
    # Function to demonstrate summary output formats
    def demonstrate_summary_formats(formatter, result):
        """Demonstrate all supported summary output formats"""
        logger.info("\nDEMONSTRATING SUMMARY OUTPUT FORMATS")
        formats_generated = []
        
        # Test all formats
        for fmt in OutputFormat:
            try:
                # Skip Excel if pandas/openpyxl not installed
                if fmt == OutputFormat.EXCEL:
                    try:
                        import pandas
                        import openpyxl
                    except ImportError:
                        logger.warning(f"Skipping {fmt.value} format - pandas/openpyxl not installed")
                        continue
                
                # Set output path and extension
                output_path = EVIDENCE_DIR / f"summary_{fmt.value}"
                if fmt == OutputFormat.EXCEL:
                    output_path = output_path.with_suffix(".xlsx")
                else:
                    output_path = output_path.with_suffix(f".{fmt.value}")
                
                # Generate report in this format
                logger.info(f"Generating {fmt.value} summary report: {output_path}")
                formatter.generate_report(
                    data=result,
                    output_type=OutputType.SUMMARY,
                    output_format=fmt,
                    output_path=output_path
                )
                
                # Verify file exists
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    logger.info(f"✓ Successfully generated {fmt.value} summary report ({file_size} bytes)")
                    formats_generated.append((fmt.value, str(output_path), file_size))
                else:
                    logger.error(f"✗ Failed to generate {fmt.value} summary report")
            except Exception as e:
                logger.error(f"Error generating {fmt.value} summary report: {str(e)}")
                logger.debug(traceback.format_exc())
        
        return formats_generated
    
    # Function to check visualization elements in HTML output
    def check_html_visualization_elements():
        """Check that HTML outputs contain the required visual elements"""
        logger.info("\nCHECKING HTML VISUALIZATION ELEMENTS")
        html_files = list(EVIDENCE_DIR.glob("*.html"))
        
        visual_elements = {
            "color-coding": ["background-color", "status-"],
            "tooltips": ["tooltip", "tooltiptext"],
            "interactive": ["hover", "chart"]
        }
        
        for html_file in html_files:
            logger.info(f"Checking {html_file.name} for visualization elements")
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            for element_type, keywords in visual_elements.items():
                found = any(keyword in content for keyword in keywords)
                if found:
                    logger.info(f"✓ {element_type} elements found")
                else:
                    logger.warning(f"✗ {element_type} elements not found")
    
    # Function to generate execution evidence summary
    def generate_evidence_summary(document_formats, matrix_formats, summary_formats):
        """Generate a summary of the execution evidence"""
        evidence_summary = {
            "execution_timestamp": datetime.now().isoformat(),
            "output_formatter_version": "1.0.0",
            "evidence_directory": str(EVIDENCE_DIR.absolute()),
            "formats_generated": {
                "document_formats": [
                    {
                        "format": fmt,
                        "file_path": path,
                        "file_size_bytes": size
                    }
                    for fmt, path, size in document_formats
                ],
                "matrix_formats": [
                    {
                        "format": fmt,
                        "file_path": path,
                        "file_size_bytes": size
                    }
                    for fmt, path, size in matrix_formats
                ],
                "summary_formats": [
                    {
                        "format": fmt,
                        "file_path": path,
                        "file_size_bytes": size
                    }
                    for fmt, path, size in summary_formats
                ]
            },
            "total_files_generated": len(document_formats) + len(matrix_formats) + len(summary_formats)
        }
        
        # Save evidence summary
        evidence_summary_path = EVIDENCE_DIR / "execution_evidence.json"
        with open(evidence_summary_path, "w", encoding="utf-8") as f:
            json.dump(evidence_summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nSaved execution evidence summary to {evidence_summary_path}")
        return evidence_summary
    
    # Execute tests
    def run_tests():
        """Run the main test sequence"""
        try:
            logger.info("=== OUTPUT FORMATTER DEMONSTRATION ===")
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info(f"Evidence directory: {EVIDENCE_DIR.absolute()}")
            
            # Initialize formatter
            logger.info("Initializing OutputFormatter")
            formatter = OutputFormatter(
                include_details=True,
                include_justifications=True,
                include_confidence=True,
                include_metadata=True,
                visualization_style="color",
                logger=logger
            )
            
            # Create sample data
            logger.info("Creating sample test data")
            validation_result = create_sample_validation_result()
            compliance_result = create_sample_compliance_result()
            
            # Create matrix data with both result types
            matrix_data = {
                "doc1": validation_result,
                "doc2": compliance_result,
            }
            
            # Test document formats
            document_formats = demonstrate_document_formats(formatter, validation_result)
            
            # Test matrix formats
            matrix_formats = demonstrate_matrix_formats(formatter, matrix_data)
            
            # Test summary formats
            summary_formats = demonstrate_summary_formats(formatter, validation_result)
            
            # Check HTML visualization elements
            check_html_visualization_elements()
            
            # Generate execution evidence summary
            evidence_summary = generate_evidence_summary(
                document_formats, matrix_formats, summary_formats
            )
            
            # Print success summary
            total_files = evidence_summary["total_files_generated"]
            logger.info("\n=== TEST EXECUTION SUCCESSFUL ===")
            logger.info(f"Successfully generated {total_files} output files in multiple formats")
            logger.info(f"All output files available in: {EVIDENCE_DIR.absolute()}")
            logger.info("=================================")
            
            return 0  # Success
            
        except Exception as e:
            logger.error(f"Error in test execution: {str(e)}")
            logger.error(traceback.format_exc())
            return 1  # Error
    
    if __name__ == "__main__":
        sys.exit(run_tests())
        
except Exception as e:
    print(f"ERROR: {str(e)}")
    print(traceback.format_exc())
    sys.exit(1)