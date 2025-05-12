# Test Document Set for TNO AI Audit Document Scanner

## Overview

This directory contains a comprehensive set of test documents designed to evaluate the TNO AI Audit Document Scanner's ability to correctly classify various document types based on their semantic content. The test set includes examples of all required and optional document types defined in the system configuration, along with edge cases to test system robustness.

## Test Set Structure

```
test_documents/
│
├── README.md                    # This file
├── TEST_DOCUMENT_SET_PLAN.md    # Overall plan and approach
├── TEST_DOCUMENT_METADATA.md    # Expected classifications and evaluation criteria
│
├── privacy_policy/              # Privacy Policy test documents
│   └── privacy_policy_template.md
│
├── dpa/                         # Data Processing Agreement test documents
│   └── data_processing_agreement_template.md
│
├── acceptable_use/              # Acceptable Use Policy test documents
│   └── acceptable_use_policy_template.md
│
├── incident_response/           # Incident Response Plan test documents
│   └── incident_response_plan_template.md
│
├── vendor_assessment/           # Vendor Security Assessment test documents
│   └── vendor_security_assessment_template.md
│
├── business_continuity/         # Business Continuity Plan test documents
│   └── business_continuity_plan_template.md
│
├── edge_cases/                  # Edge case test documents
│   ├── mixed_compliance_policy.md
│   ├── partial_password_policy.md
│   ├── empty_document.md
│   ├── quarterly_report.md
│   └── malformed_document.md
│
├── policies/                    # Existing policy documents
│   ├── corporate_information_security_policy.pdf
│   └── password_policy.pdf
│
└── audits/                      # Existing audit documents
    ├── INFORMATION SECURITY AUDIT REPORT.pdf
    ├── outdated_security_procedures.pdf
    ├── SECURITY ASSESSMENT SUMMARY.pdf
    ├── Security controls checking q1.xlsx
    └── system access review log data.xlsx
```

## Test Document Types

### Required Document Types
1. **Privacy Policy** - Document explaining how user data is collected, used, and protected
2. **Data Processing Agreement (DPA)** - Legal contract between data controller and processor
3. **Information Security Policy** - Document outlining security controls and practices
4. **Acceptable Use Policy** - Document defining acceptable use of company IT resources
5. **Incident Response Plan** - Document outlining procedures for responding to security incidents

### Optional Document Types
6. **Vendor Security Assessment** - Document evaluating security practices of third parties
7. **Security Audit Report** - Document containing findings from security audits
8. **Business Continuity Plan** - Document outlining procedures for maintaining operations during disruptions

### Edge Cases
9. **Mixed Compliance Policy** - Document containing elements of multiple document types
10. **Partial Password Policy** - Document with minimal security policy content
11. **Empty Document** - Document with essentially no content
12. **Non-Policy Document** - Document unrelated to security/compliance (quarterly report)
13. **Malformed Document** - Document with corrupted content and formatting issues

## Key Features of Test Set Design

1. **Comprehensive Coverage**: Includes all document types from configuration
2. **Key Semantic Content**: Each document contains appropriate semantic content for its type
3. **Document Format Variety**: Templates for different file formats (PDF, DOCX, XLSX)
4. **Edge Case Testing**: Documents designed to test system's robustness
5. **Clear Expected Outcomes**: Detailed metadata with expected classifications
6. **Realistic Content**: Documents mirror real-world security and compliance documentation

## Implementation Notes

The test documents are currently provided as markdown templates. For actual testing:

1. Convert templates to appropriate file formats:
   - Convert `privacy_policy_template.md` to PDF
   - Convert `data_processing_agreement_template.md` to DOCX
   - Convert `vendor_security_assessment_template.md` to XLSX
   - etc.

2. Place converted files in the appropriate directories

3. Run the TNO AI Audit Document Scanner on the test documents

4. Compare results against expected classifications in `TEST_DOCUMENT_METADATA.md`

## Next Steps

1. **Document Conversion**: Convert markdown templates to final formats (PDF, DOCX, XLSX)
2. **Test Execution**: Run the classification system on the test document set
3. **Result Analysis**: Compare actual classifications with expected outcomes
4. **System Refinement**: Adjust classification system based on test results
5. **Additional Testing**: Expand test set with more edge cases or document variations as needed

## Evaluation Criteria

See `TEST_DOCUMENT_METADATA.md` for detailed evaluation criteria and expected classifications.

## License and Usage

These test documents are proprietary to TNO and provided for internal testing purposes only. The content is synthetic and designed specifically for evaluating the document classification system.