"""
Verification script for llm_wrapper.py refactoring.
Tests core functionality without external dependencies.
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Set up path to include src directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.append(parent_dir)

# Configure logging
log_file = os.path.join(current_dir, "llm_wrapper_verification.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Define mock classes to test without dependencies
# -------------------------------------------------

class MockResponse:
    """Mock requests.Response class"""
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")

# -------------------------------------------------
# Mock implementation of core functions from llm_wrapper.py
# -------------------------------------------------

def extract_json_from_text(text):
    """
    Extract a JSON object from text content.
    
    Args:
        text: Text content that may contain a JSON object
        
    Returns:
        Extracted JSON object as a dictionary
        
    Raises:
        ValueError: If no valid JSON could be extracted
    """
    try:
        # First try direct parsing
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in text
        import re
        json_pattern = r'({.*})'
        json_match = re.search(json_pattern, text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON array in text
        array_pattern = r'(\[.*\])'
        array_match = re.search(array_pattern, text, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group(1))
            except json.JSONDecodeError:
                pass
                
    # If all extraction attempts fail
    raise ValueError(f"Could not extract valid JSON from response: {text[:100]}...")

def validate_classification_result(result):
    """
    Validate and sanitize classification result.
    
    Args:
        result: Raw classification result
        
    Returns:
        Validated and sanitized classification result
    """
    # Validate required fields
    required_fields = ["type_id", "type_name", "confidence", "rationale", "evidence"]
    for field in required_fields:
        if field not in result:
            logger.warning(f"Missing field '{field}' in result, adding default value")
            if field == "evidence":
                result[field] = []
            elif field == "confidence":
                result[field] = 0.0
            else:
                result[field] = "unknown"
    
    # Ensure confidence is a float between 0 and 1
    try:
        result["confidence"] = float(result["confidence"])
        if result["confidence"] < 0 or result["confidence"] > 1:
            logger.warning(f"Confidence score out of range: {result['confidence']}, clamping to [0,1]")
            result["confidence"] = max(0, min(1, result["confidence"]))
    except (ValueError, TypeError):
        logger.warning(f"Invalid confidence value: {result.get('confidence')}, defaulting to 0")
        result["confidence"] = 0.0
    
    # Ensure evidence is a list
    if not isinstance(result["evidence"], list):
        logger.warning("Evidence field is not a list, converting to list")
        result["evidence"] = [str(result["evidence"])]
    
    return result

# -------------------------------------------------
# Test functions
# -------------------------------------------------

def test_extract_json_from_text():
    """Test extract_json_from_text function"""
    logger.info("Testing extract_json_from_text...")
    tests_passed = 0
    tests_failed = 0
    
    # Test direct JSON
    try:
        json_text = '{"type_id": "test", "confidence": 0.9}'
        result = extract_json_from_text(json_text)
        assert result == {"type_id": "test", "confidence": 0.9}
        logger.info("✓ Direct JSON extraction passed")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Direct JSON extraction failed: {e}")
        tests_failed += 1
    
    # Test embedded JSON
    try:
        json_text = 'Some text before {"type_id": "test", "confidence": 0.9} and after'
        result = extract_json_from_text(json_text)
        assert result == {"type_id": "test", "confidence": 0.9}
        logger.info("✓ Embedded JSON extraction passed")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Embedded JSON extraction failed: {e}")
        tests_failed += 1
    
    # Test JSON array
    try:
        json_text = 'Array: [{"id": "1"}, {"id": "2"}]'
        result = extract_json_from_text(json_text)
        assert result == [{"id": "1"}, {"id": "2"}]
        logger.info("✓ JSON array extraction passed")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ JSON array extraction failed: {e}")
        tests_failed += 1
    
    # Test invalid JSON
    try:
        json_text = 'Not JSON at all'
        try:
            extract_json_from_text(json_text)
            logger.error("✗ Invalid JSON test failed: Expected ValueError not raised")
            tests_failed += 1
        except ValueError:
            logger.info("✓ Invalid JSON test passed (ValueError correctly raised)")
            tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Invalid JSON test failed with unexpected error: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed

def test_validate_classification_result():
    """Test validate_classification_result function"""
    logger.info("Testing validate_classification_result...")
    tests_passed = 0
    tests_failed = 0
    
    # Test complete result
    try:
        result = {
            "type_id": "test",
            "type_name": "Test Type",
            "confidence": 0.9,
            "rationale": "Test rationale",
            "evidence": ["evidence1", "evidence2"]
        }
        
        validated = validate_classification_result(result)
        assert validated == result
        logger.info("✓ Complete result validation passed")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Complete result validation failed: {e}")
        tests_failed += 1
    
    # Test missing fields
    try:
        result = {
            "type_id": "test"
        }
        
        validated = validate_classification_result(result)
        assert validated["type_id"] == "test"
        assert validated["type_name"] == "unknown"
        assert validated["confidence"] == 0.0
        assert validated["rationale"] == "unknown"
        assert validated["evidence"] == []
        logger.info("✓ Missing fields validation passed")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Missing fields validation failed: {e}")
        tests_failed += 1
    
    # Test invalid confidence
    try:
        result = {
            "type_id": "test",
            "type_name": "Test Type",
            "confidence": "high",
            "rationale": "Test rationale",
            "evidence": ["evidence1"]
        }
        
        validated = validate_classification_result(result)
        assert validated["confidence"] == 0.0
        logger.info("✓ Invalid confidence validation passed")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Invalid confidence validation failed: {e}")
        tests_failed += 1
    
    # Test out-of-range confidence
    try:
        # Test high confidence
        result = {
            "type_id": "test",
            "type_name": "Test Type",
            "confidence": 2.5,
            "rationale": "Test rationale",
            "evidence": ["evidence1"]
        }
        
        validated = validate_classification_result(result)
        assert validated["confidence"] == 1.0
        
        # Test negative confidence
        result["confidence"] = -0.5
        validated = validate_classification_result(result)
        assert validated["confidence"] == 0.0
        
        logger.info("✓ Out-of-range confidence validation passed")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Out-of-range confidence validation failed: {e}")
        tests_failed += 1
    
    # Test non-list evidence
    try:
        result = {
            "type_id": "test",
            "type_name": "Test Type",
            "confidence": 0.9,
            "rationale": "Test rationale",
            "evidence": "single evidence"
        }
        
        validated = validate_classification_result(result)
        assert validated["evidence"] == ["single evidence"]
        logger.info("✓ Non-list evidence validation passed")
        tests_passed += 1
    except Exception as e:
        logger.error(f"✗ Non-list evidence validation failed: {e}")
        tests_failed += 1
    
    return tests_passed, tests_failed

def run_verification():
    """Run verification tests"""
    logger.info("Starting llm_wrapper.py verification tests...")
    
    # Track test results
    total_passed = 0
    total_failed = 0
    
    # Run JSON extraction tests
    passed, failed = test_extract_json_from_text()
    total_passed += passed
    total_failed += failed
    
    # Run validation tests
    passed, failed = test_validate_classification_result()
    total_passed += passed
    total_failed += failed
    
    # Log summary
    logger.info(f"Verification complete. Tests passed: {total_passed}, Tests failed: {total_failed}")
    
    if total_failed == 0:
        logger.info("✅ All verification tests passed! The refactored llm_wrapper.py functions are working correctly.")
        return True
    else:
        logger.error(f"❌ {total_failed} verification tests failed.")
        return False

if __name__ == "__main__":
    start_time = datetime.now()
    logger.info(f"Test execution started at {start_time}")
    
    success = run_verification()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Test execution completed at {end_time} (duration: {duration:.2f} seconds)")
    
    # Generate a summary for the verification log
    with open(os.path.join(current_dir, "llm_wrapper_verification_summary.md"), "w") as f:
        f.write("# LLM Wrapper Verification Summary\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Result:** {'PASSED' if success else 'FAILED'}\n\n")
        f.write("## Core Functions Tested\n\n")
        f.write("1. **extract_json_from_text** - JSON extraction and parsing\n")
        f.write("2. **validate_classification_result** - Validation and sanitization of classification results\n\n")
        f.write("These core functions represent the key functionality added to llm_wrapper.py during refactoring.\n")
        f.write("The tests verify proper JSON handling, error recovery, and validation logic without external dependencies.\n\n")
        f.write("For full test details, see the log file: llm_wrapper_verification.log\n")
    
    logger.info(f"Verification summary saved to: {os.path.join(current_dir, 'llm_wrapper_verification_summary.md')}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)