"""
Test Execution Script for Phase 3 Components

This script runs all the unit tests for the Phase 3 components:
1. document_processor.py - Document loading and text extraction
2. llm_wrapper.py - LLM request handling and response formatting
3. main.py - Complete document classification pipeline

It captures the test results and generates a comprehensive test summary.
"""

import os
import sys
import unittest
import logging
import json
import time
from pathlib import Path
from datetime import datetime
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent / 'phase3_test_results.log')
    ]
)

logger = logging.getLogger("phase3_tests")

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, parent_dir)

# Test result summary
summary = {
    "execution_time": datetime.now().isoformat(),
    "tests_passed": 0,
    "tests_failed": 0,
    "tests_skipped": 0,
    "test_modules": {}
}

class CustomTestRunner(unittest.TextTestRunner):
    """Custom test runner that captures results for our summary"""
    
    def __init__(self, module_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = module_name
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "tests": []
        }
    
    def run(self, test):
        result = super().run(test)
        
        # Update our results dictionary
        self.results["total"] = result.testsRun
        self.results["passed"] = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        self.results["failed"] = len(result.failures) + len(result.errors)
        self.results["skipped"] = len(result.skipped)
        
        # Capture errors and failures
        for test, reason in result.errors:
            self.results["errors"].append({
                "test": str(test),
                "reason": reason,
                "type": "error"
            })
        
        for test, reason in result.failures:
            self.results["errors"].append({
                "test": str(test),
                "reason": reason,
                "type": "failure"
            })
        
        # Update summary
        summary["tests_passed"] += self.results["passed"]
        summary["tests_failed"] += self.results["failed"]
        summary["tests_skipped"] += self.results["skipped"]
        summary["test_modules"][self.module_name] = self.results
        
        return result


def load_test_module(module_name, module_path):
    """Load a test module from a path"""
    logger.info(f"Loading test module: {module_name} from {module_path}")
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            logger.error(f"Could not find module {module_name} at {module_path}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Error loading module {module_name}: {str(e)}")
        return None


def run_test_module(module_name, module_path):
    """Run tests from a specific module"""
    start_time = time.time()
    logger.info(f"Running tests for module: {module_name}")
    
    # Load the module
    module = load_test_module(module_name, module_path)
    if module is None:
        logger.error(f"Failed to load module {module_name}, skipping tests")
        return False
    
    # Create a test suite
    try:
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        
        # Run the tests with our custom runner
        runner = CustomTestRunner(
            module_name=module_name,
            verbosity=2,
            stream=sys.stdout
        )
        result = runner.run(suite)
        
        # Log results
        elapsed = time.time() - start_time
        success = result.wasSuccessful()
        status = "PASSED" if success else "FAILED"
        logger.info(f"Tests for {module_name} {status} ({elapsed:.2f}s)")
        logger.info(f"Tests run: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}, Skipped: {len(result.skipped)}")
        
        # Add to our test results
        module_results = runner.results
        module_results["time_taken"] = elapsed
        module_results["success"] = success
        module_results["test_count"] = result.testsRun
        
        return success
    except Exception as e:
        logger.error(f"Error running tests for {module_name}: {str(e)}")
        return False


def generate_test_summary():
    """Generate a markdown summary of test results"""
    summary_path = Path(__file__).parent / "phase3_test_summary.md"
    
    # Calculate totals
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    for module_name, results in summary["test_modules"].items():
        total_tests += results["total"]
        total_passed += results["passed"]
        total_failed += results["failed"]
        total_skipped += results["skipped"]
    
    # Create the markdown content
    markdown = [
        "# Phase 3 Test Execution Summary",
        "",
        f"**Execution Time:** {summary['execution_time']}",
        "",
        "## Test Summary",
        "",
        f"- **Total Tests:** {total_tests}",
        f"- **Passed:** {total_passed} ({(total_passed / total_tests * 100) if total_tests > 0 else 0:.1f}%)",
        f"- **Failed:** {total_failed}",
        f"- **Skipped:** {total_skipped}",
        f"- **Overall Status:** {'PASSED' if total_failed == 0 else 'FAILED'}",
        "",
        "## Module Results",
        ""
    ]
    
    # Add details for each module
    for module_name, results in summary["test_modules"].items():
        status = "✅ PASSED" if results["success"] else "❌ FAILED"
        time_taken = results.get("time_taken", 0)
        
        markdown.append(f"### {module_name} - {status}")
        markdown.append("")
        markdown.append(f"- **Tests:** {results['total']}")
        markdown.append(f"- **Passed:** {results['passed']}")
        markdown.append(f"- **Failed:** {results['failed']}")
        markdown.append(f"- **Skipped:** {results['skipped']}")
        markdown.append(f"- **Time:** {time_taken:.2f}s")
        markdown.append("")
        
        # Add error details if any
        if results["errors"]:
            markdown.append("#### Errors & Failures")
            markdown.append("")
            for error in results["errors"]:
                markdown.append(f"- **{error['test']}** ({error['type']})")
                markdown.append(f"  ```")
                
                # Truncate very long error messages
                reason = error['reason']
                if len(reason) > 500:
                    reason = reason[:500] + "... [truncated]"
                    
                markdown.append(f"  {reason}")
                markdown.append(f"  ```")
                markdown.append("")
    
    # Write the summary to file
    with open(summary_path, "w") as f:
        f.write("\n".join(markdown))
    
    logger.info(f"Test summary saved to: {summary_path}")
    return summary_path


def run_all_tests():
    """Run all tests for Phase 3 components"""
    logger.info("Starting Phase 3 test execution")
    
    # Track overall success
    overall_success = True
    src_dir = Path(parent_dir) / "src"
    
    # List of test modules to run
    test_modules = [
        ("test_document_processor", src_dir / "test_document_processor.py"),
        ("test_llm_wrapper", src_dir / "test_llm_wrapper.py"),
        ("test_main", src_dir / "test_main.py"),
    ]
    
    # Verification tests for each component
    verification_tests = [
        ("document_processor_verify", Path(__file__).parent / "direct_verify.py"),
        ("llm_wrapper_verify", Path(__file__).parent / "llm_wrapper_verify.py")
    ]
    
    # Run all the unit tests
    for module_name, module_path in test_modules:
        success = run_test_module(module_name, module_path)
        overall_success = overall_success and success
    
    # Run verification tests
    for module_name, module_path in verification_tests:
        if module_path.exists():
            logger.info(f"Running verification test: {module_name}")
            
            try:
                # Execute the verification script directly
                with open(module_path, 'r') as f:
                    code = compile(f.read(), module_path, 'exec')
                    exec(code)
                    
                logger.info(f"Verification test {module_name} completed")
            except Exception as e:
                logger.error(f"Error running verification test {module_name}: {str(e)}")
                overall_success = False
        else:
            logger.warning(f"Verification test {module_name} not found at {module_path}")
    
    # Generate test summary
    summary_path = generate_test_summary()
    
    # Log final status
    if overall_success:
        logger.info("✅ ALL TESTS PASSED - Phase 3 components are working correctly!")
    else:
        logger.error("❌ SOME TESTS FAILED - Check the test summary for details")
    
    return overall_success


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test execution interrupted")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error during test execution: {str(e)}")
        sys.exit(1)