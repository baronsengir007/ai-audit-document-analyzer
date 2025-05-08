"""
Test execution script for document_processor.py unit tests.
Runs the tests and captures results to a log file.
"""

import os
import sys
import unittest
from pathlib import Path
import logging
from datetime import datetime

# Set up path to include src directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.append(parent_dir)

# Configure logging
log_file = os.path.join(current_dir, "document_processor_test_results.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_basic_tests():
    """Run basic document_processor.py unit tests"""
    import tempfile
    from unittest import TestCase
    from unittest.mock import patch, MagicMock
    from pathlib import Path
    import sys
    
    # Import DocumentProcessor directly to avoid dependencies in test_document_processor.py
    try:
        from src.document_processor import DocumentProcessor
        from src.interfaces import Document
        
        # Create a simple test case class
        class BasicDocumentProcessorTests(TestCase):
            """Basic tests for DocumentProcessor class"""
            
            def setUp(self):
                """Set up test fixtures"""
                self.processor = DocumentProcessor()
                
                # Create temp directory for test files
                self.temp_dir = tempfile.TemporaryDirectory()
                self.test_dir = Path(self.temp_dir.name)
                
                # Create test file paths
                self.pdf_path = self.test_dir / "test.pdf"
                self.docx_path = self.test_dir / "test.docx"
                self.xlsx_path = self.test_dir / "test.xlsx"
                
                # Touch files to create them
                self.pdf_path.touch()
                self.docx_path.touch()
                self.xlsx_path.touch()
            
            def tearDown(self):
                """Clean up after tests"""
                self.temp_dir.cleanup()
            
            def test_process_document(self):
                """Test process_document method"""
                with patch.object(self.processor, 'extract_text', return_value="Test content"):
                    with patch.object(self.processor, '_extract_metadata', return_value={"test": "metadata"}):
                        doc = self.processor.process_document(self.pdf_path)
                        self.assertIsInstance(doc, Document)
                        self.assertEqual(doc.filename, "test.pdf")
                        self.assertEqual(doc.content, "Test content")
                        self.assertEqual(doc.metadata, {"test": "metadata"})
                        self.assertEqual(doc.source_path, str(self.pdf_path))
            
            def test_extract_text_file_type_handling(self):
                """Test extract_text file type handling"""
                with patch.object(self.processor, 'extract_text_from_pdf', return_value="PDF content"):
                    with patch.object(self.processor, 'extract_text_from_word', return_value="DOCX content"):
                        with patch.object(self.processor, 'extract_text_from_excel', return_value="XLSX content"):
                            pdf_content = self.processor.extract_text(self.pdf_path)
                            docx_content = self.processor.extract_text(self.docx_path)
                            xlsx_content = self.processor.extract_text(self.xlsx_path)
                            
                            self.assertEqual(pdf_content, "PDF content")
                            self.assertEqual(docx_content, "DOCX content")
                            self.assertEqual(xlsx_content, "XLSX content")
        
        # Create a test suite and run it
        suite = unittest.TestLoader().loadTestsFromTestCase(BasicDocumentProcessorTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        
        # Report results
        logger.info(f"Tests run: {result.testsRun}")
        logger.info(f"Errors: {len(result.errors)}")
        logger.info(f"Failures: {len(result.failures)}")
        
        # Log any errors
        if result.errors:
            logger.error("Test errors:")
            for test, error in result.errors:
                logger.error(f"{test}: {error}")
        
        # Log any failures
        if result.failures:
            logger.error("Test failures:")
            for test, failure in result.failures:
                logger.error(f"{test}: {failure}")
        
        # Log success message if all tests passed
        if result.wasSuccessful():
            logger.info("All basic document_processor tests passed successfully!")
            return True
        else:
            logger.error("Basic document_processor tests failed!")
            return False
    
    except ImportError as e:
        logger.error(f"Error importing DocumentProcessor: {e}")
        return False

def run_tests():
    """Run document_processor unit tests"""
    logger.info("Starting document_processor.py unit tests")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Source directory: {src_dir}")
    
    # Try to run full test suite
    try:
        from src.test_document_processor import TestDocumentProcessor
        
        # Create a test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestDocumentProcessor)
        
        # Run the tests and capture results
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        
        # Log test results
        logger.info(f"Tests run: {result.testsRun}")
        logger.info(f"Errors: {len(result.errors)}")
        logger.info(f"Failures: {len(result.failures)}")
        logger.info(f"Skipped: {len(result.skipped)}")
        
        # Log any errors
        if result.errors:
            logger.error("Test errors:")
            for test, error in result.errors:
                logger.error(f"{test}: {error}")
        
        # Log any failures
        if result.failures:
            logger.error("Test failures:")
            for test, failure in result.failures:
                logger.error(f"{test}: {failure}")
        
        # Log success message if all tests passed
        if result.wasSuccessful():
            logger.info("All document_processor tests passed successfully!")
            return True
        else:
            logger.error("document_processor tests failed!")
            return False
    
    except ImportError as e:
        logger.warning(f"Error importing full test suite: {e}")
        logger.info("Falling back to basic tests...")
        return run_basic_tests()
    
    except Exception as e:
        logger.error(f"Unexpected error running tests: {e}")
        return False

if __name__ == "__main__":
    start_time = datetime.now()
    logger.info(f"Test execution started at {start_time}")
    
    success = run_tests()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Test execution completed at {end_time} (duration: {duration:.2f} seconds)")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)