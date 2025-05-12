# Test Document Metadata and Expected Classifications

This file provides metadata about the test document set and lists the expected classification results for each document. It serves as a reference for evaluating the performance of the TNO AI Audit Document Scanner classification system.

## Document Set Overview

The test document set includes:
- 5 required document types
- 3 optional document types
- 5 edge cases to test system robustness

## Standard Test Documents

### Required Document Types

| Document Path | Original Format | Expected Type | Expected Confidence | Notes |
|---------------|-----------------|---------------|---------------------|-------|
| privacy_policy/privacy_policy_template.md | PDF | privacy_policy | High (>0.9) | Contains all key phrases from configuration |
| dpa/data_processing_agreement_template.md | DOCX | data_processing_agreement | High (>0.9) | Contains all key phrases from configuration |
| policies/corporate_information_security_policy.pdf | PDF | security_policy | High (>0.9) | Existing document, comprehensive security content |
| acceptable_use/acceptable_use_policy_template.md | PDF | acceptable_use_policy | High (>0.9) | Contains all key phrases from configuration |
| incident_response/incident_response_plan_template.md | DOCX | incident_response_plan | High (>0.9) | Contains all key phrases from configuration |

### Optional Document Types

| Document Path | Original Format | Expected Type | Expected Confidence | Notes |
|---------------|-----------------|---------------|---------------------|-------|
| vendor_assessment/vendor_security_assessment_template.md | XLSX | vendor_assessment | High (>0.9) | Contains all key phrases from configuration |
| business_continuity/business_continuity_plan_template.md | PDF | business_continuity_plan | High (>0.9) | Contains all key phrases from configuration |
| audits/INFORMATION SECURITY AUDIT REPORT.pdf | PDF | audit_report | High (>0.8) | Existing document, clear audit report content |

## Edge Case Test Documents

| Document Path | Original Format | Expected Type | Expected Confidence | Testing Purpose |
|---------------|-----------------|---------------|---------------------|----------------|
| edge_cases/mixed_compliance_policy.md | PDF | Multiple or uncertain | Medium (0.5-0.7) | Tests ability to handle documents with mixed content types |
| edge_cases/partial_password_policy.md | PDF | security_policy | Low (0.3-0.5) | Tests ability to classify with minimal relevant content |
| edge_cases/empty_document.md | PDF | Error or unclassified | Very low (<0.3) | Tests handling of documents with no meaningful content |
| edge_cases/quarterly_report.md | PDF | Unclassified or low confidence | Very low (<0.3) | Tests ability to identify non-policy documents |
| edge_cases/malformed_document.md | PDF | Error or partial match | Low with warning | Tests error handling for malformed content |

## Evaluation Criteria

The document classification system should:

1. **Correctly classify standard documents** with high confidence (>0.8)
2. **Provide appropriate confidence scores** that reflect classification certainty
3. **Extract relevant evidence** from the documents supporting the classification
4. **Handle edge cases gracefully** with appropriate error messages or low confidence indicators
5. **Identify unclassifiable documents** rather than forcing classification

## Expected Classification Evidence

For proper classification, the system should identify these key elements from each document type:

### Privacy Policy
- Data collection statements
- Data processing principles
- Data subject rights
- GDPR/privacy law references

### Data Processing Agreement
- Controller-processor relationship
- Data handling instructions
- Security measures
- Breach notification procedures

### Information Security Policy
- Access control requirements
- Password management
- Data protection measures
- Incident response procedures

### Acceptable Use Policy
- Authorized use statements
- Prohibited activities
- Software installation rules
- Monitoring statements

### Incident Response Plan
- Incident notification procedures
- Severity classifications
- Response team composition
- Evidence preservation guidelines

### Vendor Assessment
- Security control evaluations
- Vendor access restrictions
- Certification verification
- Risk ratings

### Business Continuity Plan
- Recovery procedures
- System restoration priorities
- Testing requirements
- Business impact analysis

### Audit Report
- Vulnerability findings
- Control evaluations
- Framework references
- Remediation recommendations

## Test Execution Instructions

When testing with these documents:

1. Convert templates to appropriate file formats (PDF, DOCX, XLSX)
2. Process documents through the classification system
3. Compare actual classification results with expected results
4. Note any discrepancies in classification type or confidence level
5. Evaluate evidence extraction quality
6. Document system handling of edge cases
7. Track performance metrics (accuracy, precision, recall)

## Test Results Documentation

For each test document, record:
- Actual classification result
- Confidence score
- Extracted evidence
- Processing time
- Any errors or warnings
- Comparison to expected results

This data will be used to evaluate the overall performance of the classification system and identify areas for improvement.