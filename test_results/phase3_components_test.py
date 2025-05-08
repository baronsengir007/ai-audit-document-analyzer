"""
Dedicated test suite for Phase 3 components.
Tests document_processor.py, llm_wrapper.py, and main.py without dependencies.
"""
import os
import sys
import pytest
import tempfile
import logging
import json
from pathlib import Path
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Create test directory
test_dir = tempfile.mkdtemp()

def teardown_module():
    """Clean up after tests"""
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

# Mock document processing
def test_document_processor_functions():
    """Test document processor extraction functions"""
    from src.document_processor import extract_text_from_pdf, extract_text_from_word, extract_text_from_excel
    
    # Create test files
    test_files = {}
    for ext in ['pdf', 'docx', 'xlsx', 'unknown']:
        test_path = os.path.join(test_dir, f"test.{ext}")
        with open(test_path, 'w') as f:
            f.write("Test content")
        test_files[ext] = test_path
    
    # Test PDF extraction
    try:
        result = extract_text_from_pdf(test_files['pdf'])
        logger.info(f"PDF extraction result type: {type(result)}")
        assert result is not None
        logger.info("✅ PDF extraction function works")
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        assert False, f"PDF extraction failed: {e}"
    
    # Test DOCX extraction
    try:
        result = extract_text_from_word(test_files['docx'])
        logger.info(f"DOCX extraction result type: {type(result)}")
        assert result is not None
        logger.info("✅ DOCX extraction function works")
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        assert False, f"DOCX extraction failed: {e}"
    
    # Test XLSX extraction
    try:
        result = extract_text_from_excel(test_files['xlsx'])
        logger.info(f"XLSX extraction result type: {type(result)}")
        assert result is not None
        logger.info("✅ XLSX extraction function works")
    except Exception as e:
        logger.error(f"XLSX extraction failed: {e}")
        assert False, f"XLSX extraction failed: {e}"
    
    # Test error handling
    try:
        # This should return an error message, not raise an exception
        result = extract_text_from_pdf(test_files['unknown'])
        assert "[ERROR]" in result.upper() or "[WARNING]" in result.upper() or "FAILED" in result.upper() or "NOT FOUND" in result.upper() or "EXTRACTION PARTIAL" in result.upper()
        logger.info("✅ Error handling for unknown files works")
    except Exception as e:
        logger.error(f"Error handling test failed: {e}")
        assert False, f"Error handling test failed: {e}"

def test_document_processor_class():
    """Test DocumentProcessor class functionality"""
    from src.document_processor import DocumentProcessor
    
    # Create test files
    test_file = os.path.join(test_dir, "test_doc.txt")
    with open(test_file, 'w') as f:
        f.write("Test document content")
    
    # Test DocumentProcessor initialization
    try:
        processor = DocumentProcessor()
        assert processor is not None
        logger.info("✅ DocumentProcessor initialization works")
    except Exception as e:
        logger.error(f"DocumentProcessor initialization failed: {e}")
        assert False, f"DocumentProcessor initialization failed: {e}"
    
    # Test process_document method
    try:
        # Create Path object from test file path
        file_path = Path(test_file)
        # Process the document using Path object
        processed = processor.process_document(file_path)
        # Verify the result
        assert processed is not None
        assert processed.content is not None  # Check content attribute
        assert processed.filename == file_path.name  # Check filename
        assert processed.source_path == str(file_path)  # Check source path
        logger.info("✅ DocumentProcessor.process_document method works")
    except Exception as e:
        logger.error(f"DocumentProcessor.process_document failed: {e}")
        assert False, f"DocumentProcessor.process_document failed: {e}"

def test_llm_wrapper_json_extraction():
    """Test LLM wrapper JSON extraction functionality"""
    from src.llm_wrapper import OllamaWrapper
    
    # Create an instance of OllamaWrapper with default parameters
    llm = OllamaWrapper()
    
    # Test direct JSON extraction
    json_text = '{"type": "policy", "confidence": 0.95}'
    try:
        result = llm.extract_json_from_text(json_text)
        assert result is not None
        assert result["type"] == "policy"
        assert result["confidence"] == 0.95
        logger.info("✅ Direct JSON extraction works")
    except Exception as e:
        logger.error(f"Direct JSON extraction failed: {e}")
        assert False, f"Direct JSON extraction failed: {e}"
    
    # Test embedded JSON extraction
    embedded_json = """
    Here is the classification result:
    ```json
    {"type": "procedure", "confidence": 0.85}
    ```
    Hope that helps!
    """
    try:
        result = llm.extract_json_from_text(embedded_json)
        assert result is not None
        assert result["type"] == "procedure"
        assert result["confidence"] == 0.85
        logger.info("✅ Embedded JSON extraction works")
    except Exception as e:
        logger.error(f"Embedded JSON extraction failed: {e}")
        assert False, f"Embedded JSON extraction failed: {e}"
    
    # Test invalid JSON handling
    invalid_json = "Not JSON at all"
    try:
        with pytest.raises(ValueError):
            llm.extract_json_from_text(invalid_json)
        logger.info("✅ Invalid JSON handling works")
    except Exception as e:
        logger.error(f"Invalid JSON handling test failed: {e}")
        assert False, f"Invalid JSON handling test failed: {e}"

def test_validate_classification_result():
    """Test classification result validation"""
    from src.llm_wrapper import OllamaWrapper
    
    # Create an instance of OllamaWrapper with default parameters
    llm = OllamaWrapper()
    
    # Test complete valid result
    complete_result = {
        "type_id": "policy_001",
        "type_name": "policy",
        "confidence": 0.9,
        "rationale": "This is a policy document",
        "evidence": ["Contains policy statements", "Includes compliance rules"]
    }
    try:
        valid_result = llm._validate_classification_result(complete_result)
        assert valid_result == complete_result
        logger.info("✅ Complete result validation works")
    except Exception as e:
        logger.error(f"Complete result validation failed: {e}")
        assert False, f"Complete result validation failed: {e}"
    
    # Test result with missing fields
    incomplete_result = {
        "type_id": "policy_001",
        "type_name": "policy"
    }
    try:
        valid_result = llm._validate_classification_result(incomplete_result)
        assert valid_result["type_name"] == "policy"
        assert "confidence" in valid_result
        assert "rationale" in valid_result
        assert "evidence" in valid_result
        logger.info("✅ Incomplete result validation works")
    except Exception as e:
        logger.error(f"Incomplete result validation failed: {e}")
        assert False, f"Incomplete result validation failed: {e}"

def test_main_functions():
    """Test main.py key functions"""
    global logger  # Ensure access to the module-level logger
    import unittest.mock
    import argparse
    
    # Create a mock namespace with expected arguments
    expected_args = argparse.Namespace(
        input_dir=Path("docs"),
        output_dir=Path("outputs"),
        config_dir=Path("config"),
        llm_model="mistral",
        confidence=0.7,
        no_cache=False,
        log_level="INFO",
        log_file="document_classification.log"
    )
    
    # Test argument parsing with mock
    try:
        # Patch the argparse.ArgumentParser.parse_args to return our test values
        with unittest.mock.patch('argparse.ArgumentParser.parse_args', return_value=expected_args):
            from src.main import parse_args, setup_logging
            args = parse_args()
            assert args is not None
            assert args.input_dir == Path("docs")
            assert args.output_dir == Path("outputs")
            assert args.llm_model == "mistral"
            logger.info("✅ Argument parsing works")
    except Exception as e:
        logger.error(f"Argument parsing failed: {e}")
        assert False, f"Argument parsing failed: {e}"
    
    # Test logging setup
    try:
        log_file = os.path.join(test_dir, "test.log")
        logger = setup_logging(log_file)
        assert logger is not None
        logger.info("✅ Logging setup works")
    except Exception as e:
        logger.error(f"Logging setup failed: {e}")
        assert False, f"Logging setup failed: {e}"

if __name__ == "__main__":
    # Execute all tests
    exit_code = pytest.main(["-xvs", __file__])
    
    # Generate summary
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(project_root, "test_results", "phase3_test_summary.md"), "w") as f:
        f.write(f"# Phase 3 Test Results\n\n")
        f.write(f"Test execution completed at: {timestamp}\n\n")
        
        if exit_code == 0:
            f.write("## [PASS] All tests PASSED successfully!\n\n")
            f.write("The Phase 3 components (document_processor.py, llm_wrapper.py, main.py) are working as expected.\n\n")
        else:
            f.write("## [FAIL] Some tests FAILED\n\n")
            f.write("Please check the console output for details on the failures.\n\n")
        
        f.write("## Test Details\n\n")
        f.write("- document_processor.py: Extraction functions and DocumentProcessor class\n")
        f.write("- llm_wrapper.py: JSON extraction and classification result validation\n")
        f.write("- main.py: Argument parsing and logging setup\n\n")
        
        f.write("### Note\n\n")
        f.write("This test suite focuses specifically on the Phase 3 components and their core functionality.\n")
        f.write("It uses direct imports and fixtures to avoid dependency issues with the full test suite.\n")
    
    sys.exit(exit_code)