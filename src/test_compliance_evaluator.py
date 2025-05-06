"""
Test suite for the ComplianceEvaluator class.
Tests document-requirement matching, evaluation methods, compliance scoring, and matrix generation.
"""

import unittest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile
import os
from datetime import datetime

from compliance_evaluator import (
    ComplianceEvaluator,
    ComplianceLevel,
    ComplianceResult,
    DocumentComplianceReport
)

from policy_parser import (
    ComplianceRequirement,
    RequirementType,
    RequirementPriority,
    RequirementSource
)

from policy_requirement_manager import PolicyRequirementManager
from llm_wrapper import OllamaWrapper


class TestComplianceEvaluator(unittest.TestCase):
    """Test suite for the ComplianceEvaluator class"""
    
    def setUp(self):
        """Set up test fixtures for each test method"""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Create mock requirements manager with sample requirements
        self.mock_req_manager = MagicMock(spec=PolicyRequirementManager)
        
        # Set up sample requirements
        self.sample_requirements = [
            ComplianceRequirement(
                id="REQ001",
                description="All passwords must be at least 12 characters long",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.HIGH,
                source=RequirementSource(document_section="Password Policy"),
                confidence_score=0.9,
                category="Authentication",
                keywords=["password", "length", "characters"]
            ),
            ComplianceRequirement(
                id="REQ002",
                description="User access must be reviewed monthly",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.MEDIUM,
                source=RequirementSource(document_section="Access Control"),
                confidence_score=0.85,
                category="Access Control",
                keywords=["access", "review", "monthly"]
            ),
            ComplianceRequirement(
                id="REQ003",
                description="Sharing of credentials is prohibited",
                type=RequirementType.PROHIBITED,
                priority=RequirementPriority.CRITICAL,
                source=RequirementSource(document_section="Password Policy"),
                confidence_score=0.95,
                category="Authentication",
                keywords=["credentials", "sharing", "prohibited"]
            ),
            ComplianceRequirement(
                id="REQ004",
                description="Servers should be patched monthly",
                type=RequirementType.RECOMMENDED,
                priority=RequirementPriority.MEDIUM,
                source=RequirementSource(document_section="System Maintenance"),
                confidence_score=0.8,
                category="Operations",
                keywords=["server", "patch", "monthly"]
            )
        ]
        
        # Configure mock requirements manager to return our samples
        self.mock_req_manager.get_all_requirements.return_value = self.sample_requirements
        
        # Create mock LLM
        self.mock_llm = MagicMock(spec=OllamaWrapper)
        
        # Set up the evaluator with mocks
        self.evaluator = ComplianceEvaluator(
            requirement_manager=self.mock_req_manager,
            llm=self.mock_llm,
            confidence_threshold=0.7,
            semantic_evaluation=False  # Default to keyword for predictable tests
        )
        
        # Sample documents for testing
        self.sample_documents = [
            {
                "filename": "password_policy.pdf",
                "type": "audit_rfi",
                "content": "This document describes our password policy. All passwords must be at least 12 characters long and contain special characters. User accounts are reviewed monthly to ensure compliance."
            },
            {
                "filename": "user_guidelines.pdf",
                "type": "policy_requirements",
                "content": "Guidelines for system use. Sharing of credentials is strictly forbidden. All users must have unique accounts."
            },
            {
                "filename": "network_diagram.pdf",
                "type": "project_data",
                "content": "This is a network diagram showing server connections. The diagram includes database servers, application servers, and client connections."
            }
        ]
    
    def test_find_relevant_requirements(self):
        """Test the requirement filtering and relevance matching"""
        # Test for a document that should match specific requirements
        doc = self.sample_documents[0]  # password_policy.pdf
        relevant_reqs = self.evaluator._find_relevant_requirements(doc)
        
        # It should match REQ001 (passwords) and REQ002 (access review)
        relevant_ids = [req.id for req in relevant_reqs]
        self.assertIn("REQ001", relevant_ids)
        self.assertIn("REQ002", relevant_ids)
        
        # Test for a document with specific prohibition
        doc = self.sample_documents[1]  # user_guidelines.pdf
        relevant_reqs = self.evaluator._find_relevant_requirements(doc)
        
        # It should match REQ003 (credential sharing)
        relevant_ids = [req.id for req in relevant_reqs]
        self.assertIn("REQ003", relevant_ids)
    
    def test_keyword_evaluation_fully_compliant(self):
        """Test keyword-based evaluation with fully compliant document"""
        doc = self.sample_documents[0]  # Contains password length and monthly review
        req = self.sample_requirements[0]  # Password length requirement
        
        result = self.evaluator._evaluate_compliance_keyword(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.FULLY_COMPLIANT)
        self.assertGreaterEqual(result.confidence_score, 0.8)
        self.assertEqual(result.evaluation_method, "keyword")
        self.assertEqual(len(result.matched_keywords), len(req.keywords))
        self.assertEqual(len(result.missing_keywords), 0)
    
    def test_keyword_evaluation_partially_compliant(self):
        """Test keyword-based evaluation with partially compliant document"""
        # Create document with partial match
        doc = {
            "filename": "partial_compliance.pdf",
            "type": "audit_rfi",
            "content": "Passwords need to be secure. Characters should be varied."
        }
        req = self.sample_requirements[0]  # Password length requirement
        
        result = self.evaluator._evaluate_compliance_keyword(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.PARTIALLY_COMPLIANT)
        self.assertLess(result.confidence_score, 0.8)
        self.assertGreater(len(result.matched_keywords), 0)
        self.assertGreater(len(result.missing_keywords), 0)
    
    def test_keyword_evaluation_non_compliant(self):
        """Test keyword-based evaluation with non-compliant document"""
        # Create document with no match
        doc = {
            "filename": "non_compliance.pdf",
            "type": "audit_rfi",
            "content": "This document contains no relevant information about the requirement."
        }
        req = self.sample_requirements[0]  # Password length requirement
        
        result = self.evaluator._evaluate_compliance_keyword(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.NON_COMPLIANT)
        self.assertEqual(len(result.matched_keywords), 0)
        self.assertGreater(len(result.missing_keywords), 0)
    
    def test_keyword_evaluation_prohibited_compliant(self):
        """Test keyword-based evaluation with prohibited requirement (no matches = compliant)"""
        # Create document that doesn't mention prohibited items
        doc = {
            "filename": "no_sharing.pdf",
            "type": "audit_rfi",
            "content": "Users must have individual accounts with unique passwords."
        }
        req = self.sample_requirements[2]  # Prohibition on credential sharing
        
        result = self.evaluator._evaluate_compliance_keyword(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.FULLY_COMPLIANT)
        self.assertEqual(len(result.matched_keywords), 0)
    
    def test_keyword_evaluation_prohibited_non_compliant(self):
        """Test keyword-based evaluation with prohibited requirement (matches = non-compliant)"""
        doc = self.sample_documents[1]  # user_guidelines.pdf (mentions credential sharing)
        req = self.sample_requirements[2]  # Prohibition on credential sharing
        
        result = self.evaluator._evaluate_compliance_keyword(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.NON_COMPLIANT)
        self.assertGreater(len(result.matched_keywords), 0)
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_semantic_evaluation(self, mock_make_request):
        """Test semantic evaluation using mocked LLM responses"""
        # Enable semantic evaluation
        self.evaluator.semantic_evaluation = True
        
        # Mock LLM response for compliant document
        mock_response = {
            'response': json.dumps({
                "yes_no_determination": "YES",
                "compliance_level": "fully_compliant",
                "confidence_score": 0.85,
                "justification": "The document clearly states passwords must be at least 12 characters long.",
                "matched_keywords": ["password", "length", "characters"],
                "missing_keywords": [],
                "evidence": {
                    "matching_text": "All passwords must be at least 12 characters long",
                    "context": "This document describes our password policy. All passwords must be at least 12 characters long and contain special characters."
                }
            })
        }
        mock_make_request.return_value = mock_response
        
        doc = self.sample_documents[0]  # password_policy.pdf
        req = self.sample_requirements[0]  # Password length requirement
        
        result = self.evaluator._evaluate_compliance_semantic(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.FULLY_COMPLIANT)
        self.assertEqual(result.evaluation_method, "semantic")
        self.assertIsNotNone(result.evidence)
        self.assertIn("matching_text", result.evidence)
        
        # Verify LLM was called with appropriate prompts
        mock_make_request.assert_called_once()
        args, kwargs = mock_make_request.call_args
        self.assertIn("COMPLIANCE REQUIREMENT", args[0])
        self.assertIn("REQ001", args[0])
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_semantic_evaluation_partial_compliance(self, mock_make_request):
        """Test semantic evaluation for partially compliant document"""
        # Enable semantic evaluation
        self.evaluator.semantic_evaluation = True
        
        # Mock LLM response for partially compliant document
        mock_response = {
            'response': json.dumps({
                "yes_no_determination": "PARTIAL",
                "compliance_level": "partially_compliant",
                "confidence_score": 0.75,
                "justification": "The document mentions password policies but doesn't specify the required length.",
                "matched_keywords": ["password"],
                "missing_keywords": ["length", "characters"],
                "evidence": {
                    "matching_text": "This document describes our password policy.",
                    "context": "This document describes our password policy. Passwords should be secure."
                }
            })
        }
        mock_make_request.return_value = mock_response
        
        doc = {
            "filename": "partial_policy.pdf",
            "type": "audit_rfi",
            "content": "This document describes our password policy. Passwords should be secure."
        }
        req = self.sample_requirements[0]  # Password length requirement
        
        result = self.evaluator._evaluate_compliance_semantic(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.PARTIALLY_COMPLIANT)
        self.assertEqual(result.evaluation_method, "semantic")
        self.assertEqual(len(result.matched_keywords), 1)
        self.assertEqual(len(result.missing_keywords), 2)
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_semantic_evaluation_non_compliance(self, mock_make_request):
        """Test semantic evaluation for non-compliant document"""
        # Enable semantic evaluation
        self.evaluator.semantic_evaluation = True
        
        # Mock LLM response for non-compliant document
        mock_response = {
            'response': json.dumps({
                "yes_no_determination": "NO",
                "compliance_level": "non_compliant",
                "confidence_score": 0.85,
                "justification": "The document does not mention any password length requirements.",
                "matched_keywords": [],
                "missing_keywords": ["password", "length", "characters"],
                "evidence": {
                    "matching_text": "",
                    "context": "This document covers network security but does not mention password requirements."
                }
            })
        }
        mock_make_request.return_value = mock_response
        
        doc = {
            "filename": "network_security.pdf",
            "type": "audit_rfi",
            "content": "This document covers network security but does not mention password requirements."
        }
        req = self.sample_requirements[0]  # Password length requirement
        
        result = self.evaluator._evaluate_compliance_semantic(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.NON_COMPLIANT)
        self.assertEqual(result.evaluation_method, "semantic")
        self.assertEqual(len(result.matched_keywords), 0)
        self.assertGreater(len(result.missing_keywords), 0)
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_semantic_evaluation_uncertainty(self, mock_make_request):
        """Test semantic evaluation for uncertain determination"""
        # Enable semantic evaluation
        self.evaluator.semantic_evaluation = True
        
        # Mock LLM response for uncertain determination
        mock_response = {
            'response': json.dumps({
                "yes_no_determination": "UNCERTAIN",
                "compliance_level": "indeterminate",
                "confidence_score": 0.45,
                "justification": "The document is not related to password requirements.",
                "matched_keywords": [],
                "missing_keywords": ["password", "length", "characters"],
                "evidence": {
                    "matching_text": "",
                    "context": "This is a financial report with no IT security information."
                }
            })
        }
        mock_make_request.return_value = mock_response
        
        doc = {
            "filename": "financial_report.pdf",
            "type": "financial",
            "content": "This is a financial report with quarterly earnings. Revenue increased by 12% compared to last year."
        }
        req = self.sample_requirements[0]  # Password length requirement
        
        result = self.evaluator._evaluate_compliance_semantic(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.INDETERMINATE)
        self.assertEqual(result.evaluation_method, "semantic")
        self.assertLess(result.confidence_score, 0.5)
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_semantic_prompt_structure(self, mock_make_request):
        """Test the structure of the semantic evaluation prompt"""
        # Enable semantic evaluation
        self.evaluator.semantic_evaluation = True
        
        # Mock LLM response
        mock_response = {
            'response': json.dumps({
                "yes_no_determination": "YES",
                "compliance_level": "fully_compliant",
                "confidence_score": 0.85,
                "justification": "Test justification",
                "matched_keywords": [],
                "missing_keywords": [],
                "evidence": {"matching_text": "test", "context": "test"}
            })
        }
        mock_make_request.return_value = mock_response
        
        doc = self.sample_documents[0]
        req = self.sample_requirements[0]
        
        # Call method to trigger prompt generation
        self.evaluator._evaluate_compliance_semantic(doc, req)
        
        # Verify prompt structure
        args, kwargs = mock_make_request.call_args
        prompt = args[0]
        system_prompt = args[1]
        
        # Check for critical elements in the prompt
        self.assertIn("CLEAR QUESTION: Does the following document satisfy this compliance requirement?", prompt)
        self.assertIn("Provide a definitive YES or NO answer", prompt)
        self.assertIn("yes_no_determination", prompt)
        self.assertIn("YES|NO|PARTIAL|UNCERTAIN", prompt)
        
        # Check for decision criteria section
        self.assertIn("DECISION CRITERIA:", prompt)
        self.assertIn("Answer \"YES\" if document FULLY satisfies", prompt)
        self.assertIn("Answer \"NO\" if document FAILS to satisfy", prompt)
        
        # Check system prompt focus
        self.assertIn("expert compliance auditor", system_prompt)
        self.assertIn("make clear YES/NO/PARTIAL/UNCERTAIN determinations", system_prompt)
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_semantic_evaluation_prohibited_requirement(self, mock_make_request):
        """Test semantic evaluation for prohibited requirements"""
        # Enable semantic evaluation
        self.evaluator.semantic_evaluation = True
        
        # Mock LLM response for prohibited requirement (item not found = compliant)
        mock_response = {
            'response': json.dumps({
                "yes_no_determination": "YES",  # YES means prohibited item not found
                "compliance_level": "fully_compliant",
                "confidence_score": 0.9,
                "justification": "The document does not mention credential sharing.",
                "matched_keywords": [],
                "missing_keywords": ["credentials", "sharing"],
                "evidence": {
                    "matching_text": "",
                    "context": "The document discusses individual user accounts but does not mention sharing."
                }
            })
        }
        mock_make_request.return_value = mock_response
        
        doc = {
            "filename": "security_policy.pdf",
            "type": "policy",
            "content": "This document outlines security practices. Users must have individual accounts."
        }
        req = self.sample_requirements[2]  # Prohibited credential sharing
        
        result = self.evaluator._evaluate_compliance_semantic(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.FULLY_COMPLIANT)
        self.assertEqual(result.evaluation_method, "semantic")
        
        # Now test when prohibited item IS found (non-compliant)
        mock_response = {
            'response': json.dumps({
                "yes_no_determination": "NO",  # NO means prohibited item was found
                "compliance_level": "non_compliant",
                "confidence_score": 0.95,
                "justification": "The document explicitly mentions credential sharing.",
                "matched_keywords": ["credentials", "sharing"],
                "missing_keywords": [],
                "evidence": {
                    "matching_text": "Users may share login credentials in emergency situations.",
                    "context": "The document states: Users may share login credentials in emergency situations."
                }
            })
        }
        mock_make_request.return_value = mock_response
        
        doc = {
            "filename": "emergency_procedures.pdf",
            "type": "procedure",
            "content": "Emergency procedures outline. Users may share login credentials in emergency situations."
        }
        
        result = self.evaluator._evaluate_compliance_semantic(doc, req)
        
        self.assertEqual(result.compliance_level, ComplianceLevel.NON_COMPLIANT)
        self.assertEqual(result.evaluation_method, "semantic")
        self.assertGreater(len(result.matched_keywords), 0)
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_semantic_evaluation_error_fallback(self, mock_make_request):
        """Test fallback to keyword evaluation when semantic evaluation fails"""
        # Enable semantic evaluation
        self.evaluator.semantic_evaluation = True
        
        # Make LLM raise an exception
        mock_make_request.side_effect = Exception("LLM error")
        
        doc = self.sample_documents[0]  # password_policy.pdf
        req = self.sample_requirements[0]  # Password length requirement
        
        # Should fall back to keyword evaluation
        result = self.evaluator._evaluate_compliance_semantic(doc, req)
        
        # Should still get a result
        self.assertIsNotNone(result)
        # Should be fully compliant (from keyword evaluation)
        self.assertEqual(result.compliance_level, ComplianceLevel.FULLY_COMPLIANT)
        # Method should be keyword (fallback)
        self.assertEqual(result.evaluation_method, "keyword")
    
    def test_evaluate_document(self):
        """Test comprehensive document evaluation"""
        doc = self.sample_documents[0]  # password_policy.pdf
        
        report = self.evaluator.evaluate_document(doc)
        
        self.assertIsInstance(report, DocumentComplianceReport)
        self.assertEqual(report.document_id, doc["filename"])
        self.assertIsNotNone(report.overall_compliance)
        self.assertGreater(len(report.results), 0)
        self.assertIsNotNone(report.summary)
        
        # Check metadata
        self.assertIn("total_requirements", report.metadata)
        self.assertIn("fully_compliant", report.metadata)
    
    def test_evaluate_documents(self):
        """Test evaluation of multiple documents"""
        docs = self.sample_documents
        
        reports = self.evaluator.evaluate_documents(docs)
        
        self.assertEqual(len(reports), len(docs))
        for doc in docs:
            self.assertIn(doc["filename"], reports)
            self.assertIsInstance(reports[doc["filename"]], DocumentComplianceReport)
    
    def test_generate_compliance_matrix(self):
        """Test generation of the compliance matrix"""
        docs = self.sample_documents
        reports = {}
        
        # First, evaluate each document
        for doc in docs:
            reports[doc["filename"]] = self.evaluator.evaluate_document(doc)
        
        # Then generate the matrix
        matrix = self.evaluator.generate_compliance_matrix(reports)
        
        # Verify matrix structure
        self.assertIn("documents", matrix)
        self.assertIn("requirements", matrix)
        self.assertIn("compliance_matrix", matrix)
        self.assertIn("summary", matrix)
        self.assertIn("metadata", matrix)
        
        # Verify document entries
        self.assertEqual(len(matrix["documents"]), len(docs))
        for doc_info in matrix["documents"]:
            self.assertIn("id", doc_info)
            self.assertIn("overall_compliance", doc_info)
        
        # Verify requirement entries
        self.assertGreater(len(matrix["requirements"]), 0)
        for req_info in matrix["requirements"]:
            self.assertIn("id", req_info)
            self.assertIn("description", req_info)
            self.assertIn("type", req_info)
            self.assertIn("priority", req_info)
        
        # Verify matrix entries
        self.assertEqual(len(matrix["compliance_matrix"]), len(docs))
        for matrix_entry in matrix["compliance_matrix"]:
            self.assertIn("document_id", matrix_entry)
            self.assertIn("results", matrix_entry)
            self.assertIsInstance(matrix_entry["results"], dict)
        
        # Verify summary
        self.assertIn("overall_compliance", matrix["summary"])
        self.assertIn("level", matrix["summary"]["overall_compliance"])
        self.assertIn("compliance_by_document", matrix["summary"])
        self.assertIn("compliance_by_requirement", matrix["summary"])
        self.assertIn("compliance_by_category", matrix["summary"])
    
    def test_save_compliance_matrix(self):
        """Test saving the compliance matrix to file"""
        docs = self.sample_documents[:1]  # Just one document for speed
        reports = {docs[0]["filename"]: self.evaluator.evaluate_document(docs[0])}
        matrix = self.evaluator.generate_compliance_matrix(reports)
        
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Save matrix to temp file
            self.evaluator.save_compliance_matrix(matrix, temp_path)
            
            # Verify file was created and contains valid JSON
            self.assertTrue(temp_path.exists())
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_matrix = json.load(f)
            
            # Verify structure matches
            self.assertIn("documents", loaded_matrix)
            self.assertIn("requirements", loaded_matrix)
            self.assertIn("compliance_matrix", loaded_matrix)
            self.assertIn("summary", loaded_matrix)
            
        finally:
            # Clean up
            if temp_path.exists():
                os.unlink(temp_path)
    
    def test_save_document_report(self):
        """Test saving a document report to file"""
        doc = self.sample_documents[0]
        report = self.evaluator.evaluate_document(doc)
        
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            # Save report to temp file
            self.evaluator.save_document_report(report, temp_path)
            
            # Verify file was created and contains valid JSON
            self.assertTrue(temp_path.exists())
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_report = json.load(f)
            
            # Verify structure matches
            self.assertEqual(loaded_report["document_id"], report.document_id)
            self.assertEqual(loaded_report["document_type"], report.document_type)
            self.assertEqual(loaded_report["overall_compliance"], report.overall_compliance.value)
            self.assertEqual(len(loaded_report["results"]), len(report.results))
            
        finally:
            # Clean up
            if temp_path.exists():
                os.unlink(temp_path)
    
    def test_error_handling(self):
        """Test handling of errors during evaluation"""
        # Create a document that will cause an error during evaluation
        doc = {
            "filename": "error_doc.pdf",
            "type": "unknown",
            "content": None  # This will cause an error when trying to process
        }
        
        # Evaluator should handle the error gracefully
        reports = self.evaluator.evaluate_documents([doc])
        
        # Should return an error report
        self.assertIn(doc["filename"], reports)
        error_report = reports[doc["filename"]]
        
        # Should have indeterminate compliance
        self.assertEqual(error_report.overall_compliance, ComplianceLevel.INDETERMINATE)
        self.assertIn("error", error_report.metadata)
    

if __name__ == "__main__":
    unittest.main()