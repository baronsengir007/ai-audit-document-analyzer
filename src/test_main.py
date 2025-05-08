"""
Unit tests for the main module.
Tests the complete document classification pipeline from loading to reporting.
"""
import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Import the module under test
from main import (
    DocumentClassificationPipeline,
    parse_arguments,
    main,
    setup_logging,
    load_documents,
    classify_documents,
    verify_document_types,
    generate_report
)

class TestMain(unittest.TestCase):
    """Test case for the main module functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_input_dir = Path(self.temp_dir) / "inputs"
        self.test_input_dir.mkdir(exist_ok=True)
        self.test_output_dir = Path(self.temp_dir) / "outputs"
        self.test_output_dir.mkdir(exist_ok=True)
        
        # Create a sample config file for testing
        self.test_config_path = Path(self.temp_dir) / "test_config.json"
        with open(self.test_config_path, 'w') as f:
            json.dump({
                "document_types": ["policy", "standard", "procedure"],
                "llm_settings": {
                    "model": "test_model",
                    "base_url": "http://test:1234",
                    "temperature": 0.1
                },
                "verification_settings": {
                    "required_types": ["policy", "standard"],
                    "confidence_threshold": 0.7
                }
            }, f)
        
        # Create sample document files
        self.create_sample_documents()
        
    def tearDown(self):
        """Tear down test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def create_sample_documents(self):
        """Create sample document files for testing"""
        # Create a few empty files with different extensions
        (self.test_input_dir / "sample_policy.pdf").touch()
        (self.test_input_dir / "sample_standard.docx").touch()
        (self.test_input_dir / "sample_procedure.xlsx").touch()
    
    def test_parse_arguments(self):
        """Test argument parsing functionality"""
        with patch('sys.argv', ['main.py', 
                               '--input', str(self.test_input_dir),
                               '--output', str(self.test_output_dir),
                               '--config', str(self.test_config_path)]):
            args = parse_arguments()
            
            self.assertEqual(args.input, str(self.test_input_dir))
            self.assertEqual(args.output, str(self.test_output_dir))
            self.assertEqual(args.config, str(self.test_config_path))
            self.assertFalse(args.verbose)
    
    def test_setup_logging(self):
        """Test logging setup"""
        logger = setup_logging(verbose=True)
        self.assertIsNotNone(logger)
        
        logger = setup_logging(verbose=False)
        self.assertIsNotNone(logger)
    
    @patch('main.document_loader.load_and_normalize_documents')
    def test_load_documents(self, mock_load):
        """Test document loading functionality"""
        # Mock the load_and_normalize_documents function
        mock_load.return_value = [
            {"filename": "sample_policy.pdf", "content": "test content", "type": "pdf"},
            {"filename": "sample_standard.docx", "content": "test content", "type": "docx"}
        ]
        
        # Call the function
        documents = load_documents(str(self.test_input_dir))
        
        # Verify the loader was called correctly
        mock_load.assert_called_once_with(str(self.test_input_dir))
        
        # Verify results
        self.assertEqual(len(documents), 2)
        self.assertEqual(documents[0]["filename"], "sample_policy.pdf")
    
    @patch('main.classify_document_semantically')
    def test_classify_documents(self, mock_classify):
        """Test document classification functionality"""
        # Mock the classify_document_semantically function
        mock_classify.return_value = {
            "type_name": "policy",
            "confidence": 0.85,
            "rationale": "Test rationale",
            "evidence": ["evidence1", "evidence2"]
        }
        
        # Create sample documents
        documents = [
            {"filename": "sample_policy.pdf", "content": "test content", "type": "pdf"},
            {"filename": "sample_standard.docx", "content": "test content", "type": "docx"}
        ]
        
        llm_settings = {
            "model": "test_model",
            "base_url": "http://test:1234",
            "temperature": 0.1
        }
        
        # Call the function
        classified_docs = classify_documents(documents, llm_settings)
        
        # Verify the classifier was called for each document
        self.assertEqual(mock_classify.call_count, 2)
        
        # Verify results
        self.assertEqual(len(classified_docs), 2)
        self.assertEqual(classified_docs[0]["classification"]["type_name"], "policy")
        self.assertEqual(classified_docs[0]["classification"]["confidence"], 0.85)
    
    @patch('main.verify_document_types')
    def test_verify_document_types(self, mock_verify):
        """Test document type verification functionality"""
        # Mock the verification function
        mock_verify.return_value = {
            "all_types_found": True,
            "required_types": ["policy", "standard"],
            "found_types": ["policy", "standard", "procedure"],
            "missing_types": [],
            "document_count": 3,
            "confidence": 0.85
        }
        
        # Create classified documents
        classified_docs = [
            {
                "filename": "sample_policy.pdf",
                "content": "test content",
                "type": "pdf",
                "classification": {
                    "type_name": "policy",
                    "confidence": 0.85
                }
            },
            {
                "filename": "sample_standard.docx",
                "content": "test content",
                "type": "docx",
                "classification": {
                    "type_name": "standard",
                    "confidence": 0.9
                }
            }
        ]
        
        verification_settings = {
            "required_types": ["policy", "standard"],
            "confidence_threshold": 0.7
        }
        
        # Call the function
        result = verify_document_types(classified_docs, verification_settings)
        
        # Verify results
        self.assertEqual(result["all_types_found"], True)
        self.assertEqual(result["found_types"], ["policy", "standard", "procedure"])
        self.assertEqual(result["missing_types"], [])
    
    @patch('main.ResultsVisualizer')
    def test_generate_report(self, mock_visualizer_class):
        """Test report generation functionality"""
        # Mock the ResultsVisualizer
        mock_visualizer = MagicMock()
        mock_visualizer_class.return_value = mock_visualizer
        mock_visualizer.generate_report.return_value = "test_report.json"
        
        # Create classified documents
        classified_docs = [
            {
                "filename": "sample_policy.pdf",
                "content": "test content",
                "type": "pdf",
                "classification": {
                    "type_name": "policy",
                    "confidence": 0.85
                }
            },
            {
                "filename": "sample_standard.docx",
                "content": "test content",
                "type": "docx",
                "classification": {
                    "type_name": "standard",
                    "confidence": 0.9
                }
            }
        ]
        
        verification_result = {
            "all_types_found": True,
            "required_types": ["policy", "standard"],
            "found_types": ["policy", "standard"],
            "missing_types": [],
            "document_count": 2,
            "confidence": 0.85
        }
        
        # Call the function
        report_path = generate_report(classified_docs, verification_result, str(self.test_output_dir))
        
        # Verify the visualizer was called correctly
        mock_visualizer_class.assert_called_once()
        mock_visualizer.generate_report.assert_called_once()
        
        # Verify results
        self.assertEqual(report_path, "test_report.json")
    
    @patch('main.load_documents')
    @patch('main.classify_documents')
    @patch('main.verify_document_types')
    @patch('main.generate_report')
    def test_document_classification_pipeline(self, mock_generate, mock_verify, mock_classify, mock_load):
        """Test the complete document classification pipeline"""
        # Mock the pipeline components
        mock_load.return_value = [
            {"filename": "sample_policy.pdf", "content": "test content", "type": "pdf"},
            {"filename": "sample_standard.docx", "content": "test content", "type": "docx"}
        ]
        
        mock_classify.return_value = [
            {
                "filename": "sample_policy.pdf",
                "content": "test content",
                "type": "pdf",
                "classification": {
                    "type_name": "policy",
                    "confidence": 0.85
                }
            },
            {
                "filename": "sample_standard.docx",
                "content": "test content",
                "type": "docx",
                "classification": {
                    "type_name": "standard",
                    "confidence": 0.9
                }
            }
        ]
        
        mock_verify.return_value = {
            "all_types_found": True,
            "required_types": ["policy", "standard"],
            "found_types": ["policy", "standard"],
            "missing_types": [],
            "document_count": 2,
            "confidence": 0.85
        }
        
        mock_generate.return_value = str(self.test_output_dir / "report.json")
        
        # Initialize the pipeline
        pipeline = DocumentClassificationPipeline(
            input_dir=str(self.test_input_dir),
            output_dir=str(self.test_output_dir),
            config_path=str(self.test_config_path)
        )
        
        # Run the pipeline
        result = pipeline.run()
        
        # Verify each component was called
        mock_load.assert_called_once()
        mock_classify.assert_called_once()
        mock_verify.assert_called_once()
        mock_generate.assert_called_once()
        
        # Verify results
        self.assertTrue(result["success"])
        self.assertEqual(result["documents_processed"], 2)
        self.assertTrue(result["all_types_found"])
        self.assertEqual(result["output_path"], str(self.test_output_dir / "report.json"))
    
    @patch('main.DocumentClassificationPipeline')
    def test_main_function(self, mock_pipeline_class):
        """Test the main function"""
        # Mock the pipeline
        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_pipeline.run.return_value = {
            "success": True,
            "documents_processed": 2,
            "all_types_found": True,
            "output_path": str(self.test_output_dir / "report.json")
        }
        
        # Mock the command line arguments
        with patch('sys.argv', ['main.py', 
                               '--input', str(self.test_input_dir),
                               '--output', str(self.test_output_dir),
                               '--config', str(self.test_config_path)]):
            # Call the main function
            result = main()
            
            # Verify the pipeline was created and run
            mock_pipeline_class.assert_called_once_with(
                input_dir=str(self.test_input_dir),
                output_dir=str(self.test_output_dir),
                config_path=str(self.test_config_path),
                verbose=False,
                cache=True
            )
            mock_pipeline.run.assert_called_once()
            
            # Verify results
            self.assertEqual(result, 0)  # Success exit code

    @patch('main.load_documents')
    def test_pipeline_error_handling(self, mock_load):
        """Test error handling in the pipeline"""
        # Mock an error in document loading
        mock_load.side_effect = Exception("Test error")
        
        # Initialize the pipeline
        pipeline = DocumentClassificationPipeline(
            input_dir=str(self.test_input_dir),
            output_dir=str(self.test_output_dir),
            config_path=str(self.test_config_path)
        )
        
        # Run the pipeline and expect it to handle the error
        result = pipeline.run()
        
        # Verify error handling
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Test error")
        
        # Modify the mock to raise a more specific error
        mock_load.side_effect = FileNotFoundError("Input directory not found")
        
        # Run again and verify proper handling
        result = pipeline.run()
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Input directory not found")
        self.assertEqual(result["error_type"], "FileNotFoundError")


if __name__ == "__main__":
    unittest.main()