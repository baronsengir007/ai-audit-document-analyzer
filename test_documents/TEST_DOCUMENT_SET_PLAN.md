# Test Document Set Plan

This document outlines the test document set for the TNO AI Audit Document Scanner. The test set is designed to evaluate the system's ability to correctly classify various document types based on their semantic content.

## Document Types Overview

According to our configuration, the system should classify documents into the following types:

### Required Document Types
1. Privacy Policy
2. Data Processing Agreement (DPA)
3. Information Security Policy
4. Acceptable Use Policy
5. Incident Response Plan

### Optional Document Types
6. Vendor Security Assessment
7. Security Audit Report
8. Business Continuity Plan

## Existing Test Documents

The repository already contains the following test documents:

### Policies
- `corporate_information_security_policy.pdf` - Information Security Policy
- `password_policy.pdf` - Information Security Policy (specific to passwords)

### Audits
- `INFORMATION SECURITY AUDIT REPORT.pdf` - Security Audit Report
- `outdated_security_procedures.pdf` - Security-related document
- `SECURITY ASSESSMENT SUMMARY.pdf` - Security Audit Report
- `Security controls checking q1.xlsx` - Security Assessment (Excel format)
- `system access review log data.xlsx` - Security Audit data (Excel format)

## Planned Test Documents

To complete the test set, we need to create documents for the missing types and add edge cases:

### 1. Privacy Policy (Required)
- **Filename**: `privacy_policy.pdf`
- **Format**: PDF
- **Key Elements**:
  - How user data is collected, used, and protected
  - Data processing principles
  - User rights regarding personal data
  - GDPR compliance statements
- **Expected Classification**: privacy_policy
- **Confidence**: High

### 2. Data Processing Agreement (Required)
- **Filename**: `data_processing_agreement.docx`
- **Format**: DOCX
- **Key Elements**:
  - Legal contract between data controller and processor
  - Terms for handling personal data
  - Security measures for processing
  - Data breach notification procedures
- **Expected Classification**: data_processing_agreement
- **Confidence**: High

### 3. Acceptable Use Policy (Required)
- **Filename**: `acceptable_use_policy.pdf`
- **Format**: PDF
- **Key Elements**:
  - Authorized uses of company IT resources
  - Prohibited activities
  - Software installation policies
  - Monitoring and enforcement statements
- **Expected Classification**: acceptable_use_policy
- **Confidence**: High

### 4. Incident Response Plan (Required)
- **Filename**: `incident_response_plan.docx`
- **Format**: DOCX
- **Key Elements**:
  - Incident notification procedures
  - Severity classifications
  - Response team composition
  - Evidence preservation guidelines
- **Expected Classification**: incident_response_plan
- **Confidence**: High

### 5. Vendor Security Assessment (Optional)
- **Filename**: `vendor_security_assessment.xlsx`
- **Format**: XLSX
- **Key Elements**:
  - Security control evaluations
  - Vendor access restrictions
  - Certifications verification
  - Risk ratings
- **Expected Classification**: vendor_assessment
- **Confidence**: High

### 6. Business Continuity Plan (Optional)
- **Filename**: `business_continuity_plan.pdf`
- **Format**: PDF
- **Key Elements**:
  - Disaster recovery procedures
  - System restoration priorities
  - Regular testing plans
  - Business impact analysis
- **Expected Classification**: business_continuity_plan
- **Confidence**: High

## Edge Cases

The following edge cases will test the system's robustness:

### 1. Mixed Document
- **Filename**: `mixed_compliance_policy.pdf`
- **Format**: PDF
- **Description**: Contains elements of both privacy policy and security policy
- **Challenge**: System should identify primary document type or classify with appropriate confidence levels
- **Expected Behavior**: Should identify both types or primary type with lower confidence

### 2. Minimal Content Document
- **Filename**: `partial_password_policy.pdf`
- **Format**: PDF
- **Description**: Contains only minimal mentions of password requirements
- **Challenge**: Limited relevant content
- **Expected Behavior**: Should classify as security_policy but with lower confidence

### 3. Malformed Document
- **Filename**: `malformed_document.pdf`
- **Format**: PDF
- **Description**: Corrupt or incomplete document with broken formatting
- **Challenge**: Difficult text extraction
- **Expected Behavior**: Should handle gracefully with appropriate error

### 4. Empty Document
- **Filename**: `empty_document.pdf`
- **Format**: PDF
- **Description**: Empty or minimal text
- **Challenge**: No meaningful content to classify
- **Expected Behavior**: Should handle gracefully with appropriate error

### 5. Non-Policy Document
- **Filename**: `quarterly_report.pdf`
- **Format**: PDF
- **Description**: Financial or operational report unrelated to security or compliance
- **Challenge**: Content is professional but unrelated to document types
- **Expected Behavior**: Should classify with low confidence or indicate no match

## Document Creation Approach

For each planned test document, we will:

1. Create the document in the appropriate format (PDF, DOCX, XLSX)
2. Include content that follows structure of existing test documents
3. Incorporate key phrases from configuration examples to ensure proper classification
4. Add realistic details to make documents representative of real-world examples
5. Place documents in appropriate directories within `test_documents/`

## Expected Metadata and Classification Documentation

For each test document, we will document:
- Filename and path
- Document type
- Key content elements
- Expected classification
- Expected confidence range

This metadata will be used to validate the classification results and evaluate the system's performance.