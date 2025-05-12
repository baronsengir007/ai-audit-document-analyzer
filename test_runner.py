#!/usr/bin/env python
"""
Test Runner for TNO AI Audit Document Scanner

This script replaces the verify_tests.sh bash script with a more robust
Python-based test runner. It provides several advantages:
1. Better error reporting and classification
2. Structured test results analysis
3. More reliable cross-platform execution
4. Integrated with PyTest's native capabilities

Usage:
    python test_runner.py  # Run all tests
    python test_runner.py --xml-report=report.xml  # Generate XML report
    python test_runner.py --verbose  # Show more detailed output
    python test_runner.py --test-path=test_document_classification.py  # Run specific tests
"""

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
import os
import glob
from pathlib import Path


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run tests for TNO AI Audit Document Scanner")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    parser.add_argument("--xml-report", type=str, default="test-results.xml",
                       help="Path to generate XML report (default: test-results.xml)")
    parser.add_argument("--test-path", type=str, default=None,
                       help="Specific test file or directory to run")
    parser.add_argument("--test-pattern", type=str, default="test_*.py",
                       help="Pattern to match test files")
    parser.add_argument("--summary-only", action="store_true",
                       help="Show only summary of test results")
    return parser.parse_args()


def get_test_command(args):
    """Build the pytest command based on arguments"""
    cmd = ["pytest"]
    
    # Add XML report option
    cmd.extend(["--junit-xml", args.xml_report])
    
    # Add verbosity setting
    if args.verbose:
        cmd.append("-v")
    
    # Add specific test path if provided
    if args.test_path:
        cmd.append(args.test_path)
    
    return cmd


def run_tests(cmd):
    """Run the tests using the specified command"""
    print(f"🧪 Running tests with command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print output to console
    if result.stdout:
        print("\n📄 Test output:")
        print(result.stdout)
    
    if result.stderr:
        print("\n⚠️ Test errors:")
        print(result.stderr)
    
    return result.returncode


def parse_xml_report(xml_path):
    """Parse the XML report to get detailed test results"""
    try:
        if not os.path.exists(xml_path):
            print(f"❌ XML report file not found: {xml_path}")
            return None
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Extract summary information
        failures = int(root.attrib.get('failures', 0))
        errors = int(root.attrib.get('errors', 0))
        skipped = int(root.attrib.get('skipped', 0))
        tests = int(root.attrib.get('tests', 0))
        time = float(root.attrib.get('time', 0))
        
        # Extract detailed test results
        test_results = []
        for test_case in root.findall(".//testcase"):
            test_name = f"{test_case.attrib.get('classname', '')}.{test_case.attrib.get('name', '')}"
            test_time = float(test_case.attrib.get('time', 0))
            
            # Check for failure or error
            failure = test_case.find("failure")
            error = test_case.find("error")
            skipped_elem = test_case.find("skipped")
            
            status = "PASSED"
            message = ""
            
            if failure is not None:
                status = "FAILED"
                message = failure.attrib.get('message', '')
            elif error is not None:
                status = "ERROR"
                message = error.attrib.get('message', '')
            elif skipped_elem is not None:
                status = "SKIPPED"
                message = skipped_elem.attrib.get('message', '')
            
            test_results.append({
                'name': test_name,
                'status': status,
                'time': test_time,
                'message': message
            })
        
        return {
            'summary': {
                'total': tests,
                'failures': failures,
                'errors': errors,
                'skipped': skipped,
                'time': time
            },
            'tests': test_results
        }
        
    except Exception as e:
        print(f"❌ Error parsing XML report: {e}")
        return None


def print_test_summary(results):
    """Print a summary of the test results"""
    if results is None:
        print("❓ No test results available")
        return
    
    summary = results['summary']
    print("\n📊 Test Summary:")
    print(f"Total tests: {summary['total']}")
    print(f"Passed: {summary['total'] - summary['failures'] - summary['errors'] - summary['skipped']}")
    print(f"Failed: {summary['failures']}")
    print(f"Errors: {summary['errors']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"Total time: {summary['time']:.2f} seconds")
    
    if summary['failures'] > 0 or summary['errors'] > 0:
        print("\n❌ Failed Tests:")
        for test in results['tests']:
            if test['status'] in ['FAILED', 'ERROR']:
                print(f"  - {test['name']}: {test['status']}")
                if test['message']:
                    print(f"    Message: {test['message']}")
    
    print("\n" + "=" * 60)
    if summary['failures'] > 0 or summary['errors'] > 0:
        print("❌ TESTS FAILED: Some tests did not pass!")
    else:
        print("✅ ALL TESTS PASSED: No failures or errors detected!")
    print("=" * 60)


def main():
    """Main entry point for the test runner"""
    args = parse_args()
    
    # Build and run the pytest command
    cmd = get_test_command(args)
    exit_code = run_tests(cmd)
    
    # Parse the XML report for detailed results
    if os.path.exists(args.xml_report):
        results = parse_xml_report(args.xml_report)
        print_test_summary(results)
    else:
        print(f"\n⚠️ XML report file not found: {args.xml_report}")
        print(f"❓ Test result: {'FAILED' if exit_code != 0 else 'PASSED'}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())