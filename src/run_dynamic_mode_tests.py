"""
Test runner for Dynamic Mode tests.
Executes tests demonstrating dynamic mode functionality with real/simulated documents.
"""

import unittest
import logging
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import our test class
from test_dynamic_mode import TestDynamicMode

def setup_logging():
    """Set up logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "dynamic_mode_test_run.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(log_file)),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("dynamic_mode_test_runner"), log_file

def run_tests():
    """Run the dynamic mode tests and collect results"""
    logger, log_file = setup_logging()
    logger.info("Starting Dynamic Mode Test Runner")
    
    # Create a test suite with our test class
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestDynamicMode)
    
    # Record start time
    start_time = datetime.now()
    
    # Setup test runner
    test_runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    try:
        test_result = test_runner.run(test_suite)
        success = test_result.wasSuccessful()
        
        # Record end time and calculate duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate result summary
        result_summary = {
            "timestamp": datetime.now().isoformat(),
            "test_count": test_result.testsRun,
            "success_count": test_result.testsRun - len(test_result.errors) - len(test_result.failures),
            "error_count": len(test_result.errors),
            "failure_count": len(test_result.failures),
            "duration_seconds": duration,
            "success": success
        }
        
        # Get document scenario details from test class
        test_instance = TestDynamicMode()
        
        # Setup the test environment
        TestDynamicMode.setUpClass()
        
        # Run the evidence generation test specifically
        with patch('compliance_evaluator.OllamaWrapper._make_request') as mock_make_request:
            # Configure mock to return successful responses
            mock_make_request.return_value = TestDynamicMode.mock_full_compliance_response
            
            # Call the evidence generation method
            evidence = test_instance.test_execute_evidence()
            
            # Run the full test suite method
            test_instance.test_full_test_suite(mock_make_request)
            
            # Get document counts
            document_count = len(TestDynamicMode.test_documents)
            
        # Clean up the test environment
        TestDynamicMode.tearDownClass()
        
        # Generate execution evidence
        results_dir = Path("outputs")
        results_dir.mkdir(exist_ok=True)
        
        evidence_report = {
            "test_suite": "Dynamic Mode Test Suite",
            "execution_timestamp": datetime.now().isoformat(),
            "execution_time_seconds": duration,
            "total_tests": test_result.testsRun,
            "success_count": test_result.testsRun - len(test_result.errors) - len(test_result.failures),
            "total_document_scenarios": document_count,
            "log_file": str(log_file),
            "results_summary": result_summary
        }
        
        evidence_path = results_dir / "dynamic_mode_test_evidence.json"
        with open(evidence_path, 'w') as f:
            json.dump(evidence_report, f, indent=2)
        
        # Generate document scenario report
        document_report = {
            "execution_timestamp": datetime.now().isoformat(),
            "total_document_scenarios": document_count,
            "document_scenarios": [
                {
                    "index": i+1,
                    "filename": doc.filename, 
                    "type": doc.classification,
                    "content_preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                }
                for i, doc in enumerate(TestDynamicMode.test_documents)
            ]
        }
        
        doc_report_path = results_dir / "document_scenarios.json"
        with open(doc_report_path, 'w') as f:
            json.dump(document_report, f, indent=2)
        
        # Print summary to console
        print("\n====== Test Execution Summary ======")
        print(f"Total tests run: {test_result.testsRun}")
        print(f"Tests passed: {test_result.testsRun - len(test_result.errors) - len(test_result.failures)}")
        print(f"Tests failed: {len(test_result.failures)}")
        print(f"Tests with errors: {len(test_result.errors)}")
        print(f"Execution time: {duration:.2f} seconds")
        print(f"Total document scenarios: {document_count}")
        print(f"Log file: {log_file}")
        print(f"Evidence report: {evidence_path}")
        print(f"Document scenarios report: {doc_report_path}")
        print("===================================")
        
        logger.info(f"Test execution completed in {duration:.2f} seconds")
        logger.info(f"Results saved to {evidence_path} and {doc_report_path}")
        
        return success, evidence_report, document_report
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        raise

if __name__ == "__main__":
    success, evidence_report, document_report = run_tests()
    sys.exit(0 if success else 1)