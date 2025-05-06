"""
Test suite for the DynamicModeAdapter class.
Tests dynamic policy-based document processing with real and simulated documents.
"""

import unittest
import logging
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
from typing import Dict, List, Any, Optional

from dynamic_mode_adapter import (
    DynamicModeAdapter,
    DynamicDocumentProcessor,
    DynamicValidationStrategy,
    DynamicValidationMode
)

from interfaces import (
    Document,
    ValidationResult,
    ComplianceResult,
    ValidationStatus
)

from compliance_evaluator import (
    ComplianceEvaluator,
    ComplianceLevel
)

from requirement_store import RequirementStore
from policy_parser import (
    ComplianceRequirement,
    RequirementType,
    RequirementPriority,
    RequirementSource
)

from llm_wrapper import OllamaWrapper
from policy_requirement_manager import PolicyRequirementManager


class TestDynamicMode(unittest.TestCase):
    """Test suite for dynamic mode document processing with real and simulated documents"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler("test_dynamic_mode.log"),
                logging.StreamHandler()
            ]
        )
        cls.logger = logging.getLogger("test_dynamic_mode")
        cls.logger.info("Setting up test environment")
        
        # Create temporary directory for test files
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_files_dir = Path(cls.temp_dir) / "test_files"
        cls.test_files_dir.mkdir()
        cls.output_dir = Path(cls.temp_dir) / "outputs"
        cls.output_dir.mkdir()
        
        # Set up sample requirements
        cls.sample_requirements = [
            ComplianceRequirement(
                id="REQ001",
                description="All employees must use strong passwords for their accounts",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.HIGH,
                source=RequirementSource(document_section="Access Control"),
                confidence_score=0.95,
                category="Access Control",
                keywords=["strong", "passwords", "accounts"]
            ),
            ComplianceRequirement(
                id="REQ002",
                description="Passwords shall be changed every 90 days",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.MEDIUM,
                source=RequirementSource(document_section="Access Control"),
                confidence_score=0.9,
                category="Access Control",
                keywords=["passwords", "changed", "90 days"]
            ),
            ComplianceRequirement(
                id="REQ003",
                description="Multi-factor authentication is required for remote access",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.HIGH,
                source=RequirementSource(document_section="Access Control"),
                confidence_score=0.95,
                category="Access Control",
                keywords=["multi-factor", "authentication", "remote", "access"]
            ),
            ComplianceRequirement(
                id="REQ004",
                description="Sensitive data must be encrypted at rest",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.CRITICAL,
                source=RequirementSource(document_section="Data Protection"),
                confidence_score=0.95,
                category="Data Protection",
                keywords=["sensitive", "data", "encrypted", "at rest"]
            ),
            ComplianceRequirement(
                id="REQ005",
                description="Regular backups are mandatory",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.HIGH,
                source=RequirementSource(document_section="Data Protection"),
                confidence_score=0.9,
                category="Data Protection",
                keywords=["regular", "backups", "mandatory"]
            ),
            ComplianceRequirement(
                id="REQ006",
                description="Data retention policies shall be followed",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.MEDIUM,
                source=RequirementSource(document_section="Data Protection"),
                confidence_score=0.9,
                category="Compliance",
                keywords=["data", "retention", "policies"]
            ),
            ComplianceRequirement(
                id="REQ007",
                description="Security incidents must be reported immediately",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.HIGH,
                source=RequirementSource(document_section="Incident Response"),
                confidence_score=0.95,
                category="Incident Response",
                keywords=["security", "incidents", "reported", "immediately"]
            ),
            ComplianceRequirement(
                id="REQ008",
                description="Access to server rooms must be restricted",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.MEDIUM,
                source=RequirementSource(document_section="Physical Security"),
                confidence_score=0.9,
                category="Physical Security",
                keywords=["access", "server", "rooms", "restricted"]
            ),
            ComplianceRequirement(
                id="REQ009",
                description="Security awareness training is required for all employees",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.MEDIUM,
                source=RequirementSource(document_section="Training"),
                confidence_score=0.9,
                category="Training",
                keywords=["security", "awareness", "training", "employees"]
            ),
            ComplianceRequirement(
                id="REQ010",
                description="Third-party vendors must sign security agreements",
                type=RequirementType.MANDATORY,
                priority=RequirementPriority.MEDIUM,
                source=RequirementSource(document_section="Vendor Management"),
                confidence_score=0.9,
                category="Vendor Management",
                keywords=["third-party", "vendors", "security", "agreements"]
            ),
            ComplianceRequirement(
                id="REQ011",
                description="Sharing of credentials is prohibited",
                type=RequirementType.PROHIBITED,
                priority=RequirementPriority.CRITICAL,
                source=RequirementSource(document_section="Access Control"),
                confidence_score=0.95,
                category="Access Control",
                keywords=["sharing", "credentials", "prohibited"]
            ),
            ComplianceRequirement(
                id="REQ012",
                description="Unsecured transmission of sensitive data is prohibited",
                type=RequirementType.PROHIBITED,
                priority=RequirementPriority.CRITICAL,
                source=RequirementSource(document_section="Data Protection"),
                confidence_score=0.95,
                category="Data Protection",
                keywords=["unsecured", "transmission", "sensitive", "data", "prohibited"]
            )
        ]
        
        # Initialize requirement store with sample requirements
        cls.requirement_store = RequirementStore()
        for req in cls.sample_requirements:
            cls.requirement_store.add_requirement(req)
            
        # Create mock LLM wrapper
        cls.mock_llm = MagicMock(spec=OllamaWrapper)
        
        # Set up standard mock responses for LLM
        cls.mock_full_compliance_response = {
            'response': json.dumps({
                "yes_no_determination": "YES",
                "compliance_level": "fully_compliant",
                "confidence_score": 0.9,
                "justification": "The document fully satisfies this requirement.",
                "matched_keywords": ["keyword1", "keyword2"],
                "missing_keywords": [],
                "evidence": {
                    "matching_text": "Relevant text from document",
                    "context": "Surrounding context from document"
                }
            })
        }
        
        cls.mock_partial_compliance_response = {
            'response': json.dumps({
                "yes_no_determination": "PARTIAL",
                "compliance_level": "partially_compliant",
                "confidence_score": 0.7,
                "justification": "The document partially satisfies this requirement.",
                "matched_keywords": ["keyword1"],
                "missing_keywords": ["keyword2"],
                "evidence": {
                    "matching_text": "Partial text from document",
                    "context": "Surrounding context from document"
                }
            })
        }
        
        cls.mock_non_compliance_response = {
            'response': json.dumps({
                "yes_no_determination": "NO",
                "compliance_level": "non_compliant",
                "confidence_score": 0.8,
                "justification": "The document fails to satisfy this requirement.",
                "matched_keywords": [],
                "missing_keywords": ["keyword1", "keyword2"],
                "evidence": {
                    "matching_text": "",
                    "context": "No relevant text found"
                }
            })
        }
        
        # Create sample documents for testing
        cls.create_test_documents()
        
        cls.logger.info(f"Test environment set up with {len(cls.sample_requirements)} sample requirements")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        shutil.rmtree(cls.temp_dir)
        cls.logger.info("Test environment cleaned up")
    
    @classmethod
    def create_test_documents(cls):
        """Create a set of test documents for testing dynamic mode"""
        # Create 20+ document scenarios
        cls.test_documents = []
        
        # 1. Fully compliant password policy
        cls.test_documents.append(Document(
            filename="password_policy.pdf",
            content="""Information Security Policy
            
            Access Control Requirements
            
            All employees must use strong passwords for their accounts. Password must be at least 12 characters long and include uppercase letters, lowercase letters, numbers, and special characters.
            
            Passwords shall be changed every 90 days. The system will automatically prompt users to change their passwords.
            
            Multi-factor authentication is required for remote access to ensure secure connections from outside the company network.
            
            Employees must not share their credentials with others under any circumstances.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "IT Security"},
            source_path=None
        ))
        
        # 2. Partially compliant password policy
        cls.test_documents.append(Document(
            filename="partial_password_policy.pdf",
            content="""Password Guidelines
            
            Passwords should be sufficiently complex. Users are encouraged to use strong passwords.
            
            Password rotation is recommended periodically.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "IT"},
            source_path=None
        ))
        
        # 3. Non-compliant password document
        cls.test_documents.append(Document(
            filename="weak_password_policy.pdf",
            content="""Password Guidelines
            
            Simple passwords are acceptable for non-critical systems.
            Password sharing is allowed for team accounts.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "IT"},
            source_path=None
        ))
        
        # 4. Data encryption policy (fully compliant)
        cls.test_documents.append(Document(
            filename="data_encryption_policy.pdf",
            content="""Data Protection Policy
            
            Sensitive data must be encrypted at rest using AES-256 encryption.
            All data transfers must use secure protocols such as HTTPS, SFTP, or SCP.
            Regular backups are mandatory and must be performed according to the backup schedule.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "IT Security"},
            source_path=None
        ))
        
        # 5. Data retention policy (fully compliant)
        cls.test_documents.append(Document(
            filename="data_retention_policy.pdf",
            content="""Data Retention Policy
            
            Data retention policies shall be followed for all company data.
            Financial records must be retained for 7 years.
            Customer data shall be retained according to GDPR requirements.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "Legal"},
            source_path=None
        ))
        
        # 6. Incident response policy (fully compliant)
        cls.test_documents.append(Document(
            filename="incident_response_policy.pdf",
            content="""Incident Response Policy
            
            Security incidents must be reported immediately to the security team.
            All incidents shall be documented and investigated according to their severity.
            Root cause analysis is required for major incidents to prevent recurrence.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "IT Security"},
            source_path=None
        ))
        
        # 7. Physical security policy (fully compliant)
        cls.test_documents.append(Document(
            filename="physical_security_policy.pdf",
            content="""Physical Security Policy
            
            Access to server rooms must be restricted to authorized personnel only.
            Visitors shall be escorted at all times while in the facility.
            Workstations must be locked when unattended to prevent unauthorized access.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "Facilities"},
            source_path=None
        ))
        
        # 8. Security training policy (fully compliant)
        cls.test_documents.append(Document(
            filename="security_training_policy.pdf",
            content="""Security Training Policy
            
            Security awareness training is required for all employees.
            Training shall be completed within 30 days of hire for new employees.
            Refresher training must be conducted annually for all staff.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "HR"},
            source_path=None
        ))
        
        # 9. Vendor management policy (fully compliant)
        cls.test_documents.append(Document(
            filename="vendor_management_policy.pdf",
            content="""Vendor Management Policy
            
            Third-party vendors must sign security agreements before accessing company systems.
            Vendor access shall be reviewed quarterly to ensure it remains appropriate.
            Security assessments are required for critical vendors on an annual basis.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "Procurement"},
            source_path=None
        ))
        
        # 10. Data breach notification procedure (partially compliant)
        cls.test_documents.append(Document(
            filename="data_breach_procedure.docx",
            content="""Data Breach Notification Procedure
            
            In the event of a data breach, the following steps should be taken:
            1. Assess the scope of the breach
            2. Contain the breach if possible
            3. Notify management
            
            Documentation should be maintained throughout the response process.
            """,
            classification="procedure",
            metadata={"type": "procedure", "department": "IT Security"},
            source_path=None
        ))
        
        # 11. Remote access guidelines (partially compliant)
        cls.test_documents.append(Document(
            filename="remote_access_guidelines.pdf",
            content="""Remote Access Guidelines
            
            Remote access is provided to employees who need to work outside the office.
            VPN should be used when connecting to company resources.
            Consider using multi-factor authentication for sensitive systems.
            """,
            classification="guideline",
            metadata={"type": "guideline", "department": "IT"},
            source_path=None
        ))
        
        # 12. Cloud security policy (fully compliant)
        cls.test_documents.append(Document(
            filename="cloud_security_policy.pdf",
            content="""Cloud Security Policy
            
            All cloud services must be approved by IT security before use.
            Sensitive data must be encrypted at rest in cloud storage.
            Multi-factor authentication is required for all cloud service accounts.
            Regular security assessments of cloud providers are mandatory.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "IT Security"},
            source_path=None
        ))
        
        # 13. Mobile device policy (partially compliant)
        cls.test_documents.append(Document(
            filename="mobile_device_policy.pdf",
            content="""Mobile Device Policy
            
            Company mobile devices should be password protected.
            Updates should be installed promptly when available.
            Lost or stolen devices should be reported to IT.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "IT"},
            source_path=None
        ))
        
        # 14. Network security standards (fully compliant)
        cls.test_documents.append(Document(
            filename="network_security_standards.pdf",
            content="""Network Security Standards
            
            All network traffic must be encrypted using industry-standard protocols.
            Firewalls must be implemented at network boundaries.
            Regular vulnerability scans are mandatory for all network devices.
            Sensitive data must be encrypted during transmission.
            """,
            classification="standard",
            metadata={"type": "standard", "department": "IT Security"},
            source_path=None
        ))
        
        # 15. Software development security policy (fully compliant)
        cls.test_documents.append(Document(
            filename="sdlc_security_policy.pdf",
            content="""Software Development Security Policy
            
            Security requirements must be defined at the beginning of development projects.
            Code reviews are mandatory for all code changes.
            Sensitive data must be encrypted at rest and in transit.
            Authentication mechanisms must implement multi-factor authentication for privileged access.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "Development"},
            source_path=None
        ))
        
        # 16. Data classification policy (fully compliant)
        cls.test_documents.append(Document(
            filename="data_classification_policy.pdf",
            content="""Data Classification Policy
            
            All company data must be classified according to sensitivity.
            Sensitive data must be encrypted at rest.
            Access to classified data must be strictly controlled.
            Data retention policies shall be followed based on classification level.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "IT Security"},
            source_path=None
        ))
        
        # 17. Acceptable use policy (partially compliant)
        cls.test_documents.append(Document(
            filename="acceptable_use_policy.pdf",
            content="""Acceptable Use Policy
            
            Company resources should be used for business purposes.
            Users should choose strong passwords for company accounts.
            Personal use of company resources should be limited.
            """,
            classification="policy",
            metadata={"type": "policy", "department": "HR"},
            source_path=None
        ))
        
        # 18. Employee offboarding checklist (non-compliant)
        cls.test_documents.append(Document(
            filename="offboarding_checklist.xlsx",
            content="""Employee Offboarding Checklist
            
            1. Collect company equipment
            2. Disable building access
            3. Conduct exit interview
            4. Process final paycheck
            """,
            classification="procedure",
            metadata={"type": "procedure", "department": "HR"},
            source_path=None
        ))
        
        # 19. Empty document (edge case)
        cls.test_documents.append(Document(
            filename="empty_document.pdf",
            content="",
            classification="unknown",
            metadata={"type": "unknown"},
            source_path=None
        ))
        
        # 20. Malformed document (edge case)
        cls.test_documents.append(Document(
            filename="malformed_document.pdf",
            content="This is not a properly formatted document.",
            classification="unknown",
            metadata={"type": "unknown"},
            source_path=None
        ))
        
        # 21. Unrelated business document (non-compliant)
        cls.test_documents.append(Document(
            filename="quarterly_report.pdf",
            content="""Quarterly Financial Report
            
            Revenue: $10.5M
            Expenses: $8.2M
            Profit: $2.3M
            
            This document contains financial results for Q1 2025.
            """,
            classification="report",
            metadata={"type": "report", "department": "Finance"},
            source_path=None
        ))
        
        # 22. Document with prohibited activities (non-compliant)
        cls.test_documents.append(Document(
            filename="shared_accounts_memo.pdf",
            content="""Team Accounts Memo
            
            To improve efficiency, the following shared accounts have been created:
            - admin@company.com - For administrative tasks (password: Admin123)
            - support@company.com - For customer support (password: Support123)
            
            Teams should use these shared accounts for their respective functions.
            """,
            classification="memo",
            metadata={"type": "memo", "department": "IT"},
            source_path=None
        ))
        
        # 23. Mixed compliance document (partially compliant)
        cls.test_documents.append(Document(
            filename="mixed_compliance_policy.pdf",
            content="""Security Guidelines
            
            Passwords shall be changed every 90 days.
            
            Use of personal devices for company work is acceptable without encryption.
            
            Multi-factor authentication is required for remote access.
            
            Team members may share login credentials when necessary for business operations.
            """,
            classification="guideline",
            metadata={"type": "guideline", "department": "IT"},
            source_path=None
        ))
        
        # Create files in test directory
        for doc in cls.test_documents:
            file_path = cls.test_files_dir / doc.filename
            with open(file_path, 'w') as f:
                f.write(doc.content)
            doc.source_path = file_path
        
        cls.logger.info(f"Created {len(cls.test_documents)} test documents")
        
        # Write document list to log for reference
        cls.logger.info("Test documents:")
        for i, doc in enumerate(cls.test_documents, 1):
            cls.logger.info(f"{i}. {doc.filename} - {doc.classification}")
    
    def setUp(self):
        """Set up before each test"""
        # Create a fresh dynamic mode adapter for each test
        self.dynamic_adapter = DynamicModeAdapter(
            requirement_store=self.requirement_store,
            config={"semantic_evaluation": True}
        )
        
        # Create dynamic validation mode
        self.validation_mode = DynamicValidationMode()
        self.validation_mode.initialize({
            "requirement_store": self.requirement_store,
            "llm_config": {},
            "max_workers": 2
        })
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_document_processing(self, mock_make_request):
        """Test document processing functionality"""
        self.logger.info("Testing document processing")
        
        # Configure mock to return full compliance
        mock_make_request.return_value = self.mock_full_compliance_response
        
        # Process a fully compliant document
        processor = DynamicDocumentProcessor()
        doc = self.test_documents[0]  # password_policy.pdf
        
        # Process the document
        processed_doc = processor.process_document(doc.source_path)
        
        # Verify document was processed correctly
        self.assertEqual(processed_doc.filename, doc.filename)
        self.assertEqual(processed_doc.classification, doc.classification)
        self.assertIn("content", dir(processed_doc))
        self.assertIsNotNone(processed_doc.content)
        
        self.logger.info(f"Successfully processed document: {doc.filename}")
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_validation_strategy_fully_compliant(self, mock_make_request):
        """Test validation strategy with fully compliant document"""
        self.logger.info("Testing validation strategy with fully compliant document")
        
        # Configure mock to return full compliance
        mock_make_request.return_value = self.mock_full_compliance_response
        
        # Process a fully compliant document
        strategy = DynamicValidationStrategy(requirement_store=self.requirement_store)
        doc = self.test_documents[0]  # password_policy.pdf
        
        # Validate the document
        result = strategy.validate(doc)
        
        # Verify validation result
        self.assertEqual(result.status, ValidationStatus.PASSED)
        self.assertEqual(result.document_id, doc.filename)
        self.assertGreater(len(result.categories), 0)
        
        self.logger.info(f"Validation result for {doc.filename}: {result.status}")
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_validation_strategy_partially_compliant(self, mock_make_request):
        """Test validation strategy with partially compliant document"""
        self.logger.info("Testing validation strategy with partially compliant document")
        
        # Configure mock to return partial compliance
        mock_make_request.return_value = self.mock_partial_compliance_response
        
        # Process a partially compliant document
        strategy = DynamicValidationStrategy(requirement_store=self.requirement_store)
        doc = self.test_documents[1]  # partial_password_policy.pdf
        
        # Validate the document
        result = strategy.validate(doc)
        
        # Verify validation result
        self.assertEqual(result.status, ValidationStatus.WARNING)
        self.assertEqual(result.document_id, doc.filename)
        
        self.logger.info(f"Validation result for {doc.filename}: {result.status}")
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_validation_strategy_non_compliant(self, mock_make_request):
        """Test validation strategy with non-compliant document"""
        self.logger.info("Testing validation strategy with non-compliant document")
        
        # Configure mock to return non-compliance
        mock_make_request.return_value = self.mock_non_compliance_response
        
        # Process a non-compliant document
        strategy = DynamicValidationStrategy(requirement_store=self.requirement_store)
        doc = self.test_documents[2]  # weak_password_policy.pdf
        
        # Validate the document
        result = strategy.validate(doc)
        
        # Verify validation result
        self.assertEqual(result.status, ValidationStatus.FAILED)
        self.assertEqual(result.document_id, doc.filename)
        
        self.logger.info(f"Validation result for {doc.filename}: {result.status}")
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_validation_mode_batch_processing(self, mock_make_request):
        """Test batch processing of documents"""
        self.logger.info("Testing batch processing of documents")
        
        # Configure mock responses based on document type
        def mock_response_selector(*args, **kwargs):
            prompt = args[0]
            if "strong passwords" in prompt and "password_policy.pdf" in prompt:
                return self.mock_full_compliance_response
            elif "partial_password_policy.pdf" in prompt:
                return self.mock_partial_compliance_response
            else:
                return self.mock_non_compliance_response
        
        mock_make_request.side_effect = mock_response_selector
        
        # Select a subset of documents for batch testing
        batch_docs = self.test_documents[:3]  # 3 password policies with different compliance levels
        
        # Process batch
        results = self.validation_mode.process_batch(batch_docs)
        
        # Verify batch results
        self.assertEqual(len(results), len(batch_docs))
        self.assertEqual(results[0].status, ValidationStatus.PASSED)  # Fully compliant
        self.assertEqual(results[1].status, ValidationStatus.WARNING)  # Partially compliant
        self.assertEqual(results[2].status, ValidationStatus.FAILED)  # Non-compliant
        
        self.logger.info(f"Successfully processed batch of {len(batch_docs)} documents")
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_save_validation_results(self, mock_make_request):
        """Test saving validation results"""
        self.logger.info("Testing saving validation results")
        
        # Configure mock to return mixed responses
        def mock_response_selector(*args, **kwargs):
            prompt = args[0]
            if "password_policy.pdf" in prompt:
                return self.mock_full_compliance_response
            elif "partial_password_policy.pdf" in prompt:
                return self.mock_partial_compliance_response
            else:
                return self.mock_non_compliance_response
        
        mock_make_request.side_effect = mock_response_selector
        
        # Select a subset of documents
        batch_docs = self.test_documents[:3]  # 3 password policies with different compliance levels
        
        # Process batch
        results = self.validation_mode.process_batch(batch_docs)
        
        # Save results
        output_path = self.output_dir / "validation_results.json"
        self.validation_mode.save_results(results, output_path)
        
        # Verify saved results
        self.assertTrue(output_path.parent.exists())
        summary_path = output_path.parent / "dynamic_validation_summary.json"
        self.assertTrue(summary_path.exists())
        
        # Check summary content
        with open(summary_path, 'r') as f:
            summary = json.load(f)
            self.assertEqual(summary["total_documents"], len(batch_docs))
            self.assertEqual(summary["passed_documents"], 1)
            self.assertEqual(summary["failed_documents"], 1)
            self.assertEqual(summary["warning_documents"], 1)
        
        self.logger.info(f"Successfully saved validation results to {output_path}")
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_dynamic_adapter_process(self, mock_make_request):
        """Test DynamicModeAdapter process method"""
        self.logger.info("Testing DynamicModeAdapter process method")
        
        # Configure mock to return full compliance
        mock_make_request.return_value = self.mock_full_compliance_response
        
        # Process a fully compliant document
        doc = self.test_documents[0]  # password_policy.pdf
        
        # Process with dynamic adapter
        result = self.dynamic_adapter.process(doc)
        
        # Verify result
        self.assertIsInstance(result, ComplianceResult)
        self.assertTrue(result.is_compliant)
        self.assertGreater(result.confidence, 0.7)
        self.assertEqual(result.mode_used, "dynamic")
        
        self.logger.info(f"Successfully processed document with DynamicModeAdapter: {doc.filename}")
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_process_multiple_document_types(self, mock_make_request):
        """Test processing different document types"""
        self.logger.info("Testing processing different document types")
        
        # Configure mock responses
        def mock_response_selector(*args, **kwargs):
            prompt = args[0]
            if "encrypted" in prompt and "data_encryption_policy.pdf" in prompt:
                return self.mock_full_compliance_response
            elif "acceptable_use_policy.pdf" in prompt:
                return self.mock_partial_compliance_response
            elif "offboarding_checklist.xlsx" in prompt:
                return self.mock_non_compliance_response
            else:
                return self.mock_partial_compliance_response
        
        mock_make_request.side_effect = mock_response_selector
        
        # Test documents of different types
        docs = [
            self.test_documents[3],  # data_encryption_policy.pdf
            self.test_documents[16],  # acceptable_use_policy.pdf
            self.test_documents[17]   # offboarding_checklist.xlsx
        ]
        
        results = []
        for doc in docs:
            result = self.dynamic_adapter.process(doc)
            results.append(result)
            self.logger.info(f"Processed {doc.filename}: {result.is_compliant}, confidence: {result.confidence}")
        
        # Verify results
        self.assertTrue(results[0].is_compliant)  # Fully compliant
        self.assertTrue(results[1].is_compliant)  # Partially compliant (still passes)
        self.assertFalse(results[2].is_compliant)  # Non-compliant
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_prohibited_requirements(self, mock_make_request):
        """Test handling of prohibited requirements"""
        self.logger.info("Testing handling of prohibited requirements")
        
        # Configure mock responses
        def mock_response_selector(*args, **kwargs):
            prompt = args[0]
            if "sharing of credentials" in prompt and "shared_accounts_memo.pdf" in prompt:
                return {
                    'response': json.dumps({
                        "yes_no_determination": "NO",  # NO for prohibited means found (non-compliant)
                        "compliance_level": "non_compliant",
                        "confidence_score": 0.95,
                        "justification": "The document explicitly mentions sharing credentials.",
                        "matched_keywords": ["sharing", "credentials"],
                        "missing_keywords": [],
                        "evidence": {
                            "matching_text": "Teams should use these shared accounts for their respective functions.",
                            "context": "Surrounding context from document"
                        }
                    })
                }
            else:
                return self.mock_full_compliance_response
        
        mock_make_request.side_effect = mock_response_selector
        
        # Test document with prohibited activities
        doc = self.test_documents[21]  # shared_accounts_memo.pdf
        
        # Process with dynamic adapter
        result = self.dynamic_adapter.process(doc)
        
        # Verify result
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.logger.info(f"Successfully identified prohibited activity in {doc.filename}")
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_edge_case_empty_document(self, mock_make_request):
        """Test handling of empty document edge case"""
        self.logger.info("Testing handling of empty document edge case")
        
        # Configure mock to return an error-like response
        mock_make_request.side_effect = Exception("Empty document content")
        
        # Process an empty document
        doc = self.test_documents[18]  # empty_document.pdf
        
        # Process with dynamic adapter
        result = self.dynamic_adapter.process(doc)
        
        # Verify result
        self.assertIsInstance(result, ComplianceResult)
        self.assertFalse(result.is_compliant)
        self.assertEqual(result.mode_used, "dynamic_error")
        self.assertIn("error", result.details)
        
        self.logger.info(f"Successfully handled empty document: {doc.filename}")
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_comprehensive_policy_evaluation(self, mock_make_request):
        """Test comprehensive policy evaluation"""
        self.logger.info("Testing comprehensive policy evaluation")
        
        # Configure mock responses for different requirements
        requirement_responses = {
            "REQ001": self.mock_full_compliance_response,  # Strong passwords
            "REQ002": self.mock_full_compliance_response,  # Password changes
            "REQ003": self.mock_full_compliance_response,  # MFA
            "REQ004": self.mock_full_compliance_response,  # Encryption
            "REQ011": {  # Prohibited credential sharing (compliance = not found)
                'response': json.dumps({
                    "yes_no_determination": "YES",
                    "compliance_level": "fully_compliant",
                    "confidence_score": 0.9,
                    "justification": "No credential sharing mentioned positively.",
                    "matched_keywords": [],
                    "missing_keywords": ["sharing", "credentials"],
                    "evidence": {
                        "matching_text": "Employees must not share their credentials with others.",
                        "context": "Surrounding context from document"
                    }
                })
            }
        }
        
        def mock_response_for_requirement(*args, **kwargs):
            prompt = args[0]
            for req_id, response in requirement_responses.items():
                if req_id in prompt:
                    return response
            return self.mock_partial_compliance_response
        
        mock_make_request.side_effect = mock_response_for_requirement
        
        # Test comprehensive policy document
        doc = self.test_documents[0]  # password_policy.pdf
        
        # Process with dynamic adapter
        result = self.dynamic_adapter.process(doc)
        
        # Verify result
        self.assertIsInstance(result, ComplianceResult)
        self.assertTrue(result.is_compliant)
        self.assertGreater(result.confidence, 0.8)
        
        # Verify details
        self.assertIn("requirement_results", result.details)
        requirement_results = result.details["requirement_results"]
        
        # Log detailed results
        self.logger.info(f"Comprehensive evaluation of {doc.filename}:")
        for req_id, req_result in requirement_results.items():
            self.logger.info(f"  {req_id}: {req_result['compliance_level']}, confidence: {req_result['confidence_score']}")
    
    @patch('compliance_evaluator.OllamaWrapper._make_request')
    def test_full_test_suite(self, mock_make_request):
        """Run all document scenarios through dynamic mode and report results"""
        self.logger.info("Running full test suite with all document scenarios")
        
        # Configure mock responses based on document content patterns
        def mock_compliance_response(*args, **kwargs):
            prompt = args[0]
            doc_content = prompt.split("Content:")[1].split("[truncated")[0] if "Content:" in prompt else ""
            
            # Determine compliance based on document content patterns
            if any(phrase in doc_content for phrase in [
                "must be at least 12 characters", 
                "mandatory", 
                "required",
                "shall be"
            ]) and "REQ" in prompt:
                return self.mock_full_compliance_response
                
            elif any(phrase in doc_content for phrase in [
                "should be", 
                "encouraged", 
                "recommended", 
                "consider"
            ]) and "REQ" in prompt:
                return self.mock_partial_compliance_response
                
            elif any(phrase in doc_content for phrase in [
                "sharing of credentials", 
                "shared accounts",
                "simple passwords are acceptable",
                "personal devices"
            ]) and "prohibited" in prompt.lower():
                return {
                    'response': json.dumps({
                        "yes_no_determination": "NO",
                        "compliance_level": "non_compliant",
                        "confidence_score": 0.9,
                        "justification": "The document mentions prohibited activities.",
                        "matched_keywords": ["sharing", "credentials"],
                        "missing_keywords": [],
                        "evidence": {
                            "matching_text": "Found prohibited content",
                            "context": "Document context"
                        }
                    })
                }
                
            elif "empty_document.pdf" in prompt or "malformed_document.pdf" in prompt:
                raise Exception("Empty or malformed document")
                
            else:
                return self.mock_non_compliance_response
        
        mock_make_request.side_effect = mock_compliance_response
        
        # Run all documents through dynamic mode
        results = []
        all_passed = True
        
        # Process each document
        for i, doc in enumerate(self.test_documents):
            try:
                result = self.dynamic_adapter.process(doc)
                results.append((doc.filename, result.is_compliant, result.confidence))
                
                # Log result
                outcome = "PASSED" if result.is_compliant else "FAILED"
                self.logger.info(f"Test {i+1}/{len(self.test_documents)}: {doc.filename} - {outcome} (confidence: {result.confidence:.2f})")
                
                # Save detailed result for evidence
                result_path = self.output_dir / f"{doc.filename}_result.json"
                with open(result_path, 'w') as f:
                    json.dump({
                        "filename": doc.filename,
                        "is_compliant": result.is_compliant,
                        "confidence": result.confidence,
                        "mode_used": result.mode_used,
                        "details": result.details
                    }, f, indent=2)
                
            except Exception as e:
                self.logger.error(f"Error processing {doc.filename}: {str(e)}")
                results.append((doc.filename, False, 0.0))
                all_passed = False
        
        # Generate summary report
        summary = {
            "test_timestamp": datetime.now().isoformat(),
            "total_documents": len(self.test_documents),
            "passed_documents": sum(1 for _, is_compliant, _ in results if is_compliant),
            "failed_documents": sum(1 for _, is_compliant, _ in results if not is_compliant),
            "average_confidence": sum(conf for _, _, conf in results) / len(results),
            "all_tests_passed": all_passed,
            "results": [
                {"filename": filename, "is_compliant": is_compliant, "confidence": conf}
                for filename, is_compliant, conf in results
            ]
        }
        
        # Save summary report
        summary_path = self.output_dir / "dynamic_mode_test_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Output summary to log
        self.logger.info("====== Test Suite Summary ======")
        self.logger.info(f"Total documents tested: {summary['total_documents']}")
        self.logger.info(f"Passed: {summary['passed_documents']}")
        self.logger.info(f"Failed: {summary['failed_documents']}")
        self.logger.info(f"Average confidence: {summary['average_confidence']:.2f}")
        self.logger.info(f"All tests passed: {summary['all_tests_passed']}")
        self.logger.info("================================")
        
        # Verify summary contains valid data
        self.assertEqual(summary['total_documents'], len(self.test_documents))
        self.assertGreater(summary['passed_documents'], 0)
        
        # Verify output directory contains results
        result_files = list(self.output_dir.glob("*_result.json"))
        self.assertEqual(len(result_files), len(self.test_documents))
    
    def test_execute_evidence(self):
        """Execute test suite and generate evidence of execution"""
        self.logger.info("Executing test suite to generate evidence")
        
        # Record start time
        start_time = datetime.now()
        
        # Execute key test methods to generate evidence
        with patch('compliance_evaluator.OllamaWrapper._make_request') as mock_make_request:
            mock_make_request.return_value = self.mock_full_compliance_response
            
            # Run core test methods
            self.test_document_processing(mock_make_request)
            self.test_validation_strategy_fully_compliant(mock_make_request)
            self.test_dynamic_adapter_process(mock_make_request)
            
            # Update mock for different responses
            def mixed_responses(*args, **kwargs):
                prompt = args[0]
                if "password_policy.pdf" in prompt:
                    return self.mock_full_compliance_response
                elif "partial" in prompt:
                    return self.mock_partial_compliance_response
                else:
                    return self.mock_non_compliance_response
            
            mock_make_request.side_effect = mixed_responses
            
            # Run batch test
            self.test_validation_mode_batch_processing(mock_make_request)
            self.test_save_validation_results(mock_make_request)
            
            # Run the full test suite
            mock_make_request.side_effect = lambda *args, **kwargs: self.mock_full_compliance_response
            self.test_full_test_suite(mock_make_request)
        
        # Record end time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Generate execution evidence
        evidence = {
            "test_suite": "Dynamic Mode Test Suite",
            "execution_timestamp": datetime.now().isoformat(),
            "execution_time_seconds": execution_time,
            "total_tests": len([m for m in dir(self) if m.startswith('test_')]),
            "total_document_scenarios": len(self.test_documents),
            "log_file": "test_dynamic_mode.log",
            "results_directory": str(self.output_dir),
            "summary_file": str(self.output_dir / "dynamic_mode_test_summary.json")
        }
        
        # Save execution evidence
        evidence_path = self.output_dir / "execution_evidence.json"
        with open(evidence_path, 'w') as f:
            json.dump(evidence, f, indent=2)
        
        # Log execution evidence
        self.logger.info("====== Execution Evidence ======")
        self.logger.info(f"Test suite: {evidence['test_suite']}")
        self.logger.info(f"Executed at: {evidence['execution_timestamp']}")
        self.logger.info(f"Execution time: {evidence['execution_time_seconds']:.2f} seconds")
        self.logger.info(f"Total tests: {evidence['total_tests']}")
        self.logger.info(f"Document scenarios: {evidence['total_document_scenarios']}")
        self.logger.info(f"Log file: {evidence['log_file']}")
        self.logger.info(f"Results directory: {evidence['results_directory']}")
        self.logger.info(f"Summary file: {evidence['summary_file']}")
        self.logger.info("=================================")
        
        # Verify evidence file exists
        self.assertTrue(evidence_path.exists())
        
        # Return evidence for caller
        return evidence


if __name__ == "__main__":
    # Configure logging
    log_file = "test_dynamic_mode.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("test_dynamic_mode_main")
    logger.info("Starting Dynamic Mode Test Suite execution")
    
    try:
        # Run the tests
        unittest.main()
    except SystemExit:
        # unittest.main() calls sys.exit(), catch it to add final log message
        logger.info("Dynamic Mode Test Suite completed")