# 🧠 TNO AI Audit Document Scanner

## 📋 Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Quick Start Guide](#-quick-start-guide)
- [Detailed Usage Guide](#-detailed-usage-guide)
- [Usage Examples](#-usage-examples)
  - [Static Mode Examples](#static-mode-examples)
  - [Dynamic Mode Examples](#dynamic-mode-examples)
  - [Unified Workflow Examples](#unified-workflow-examples)
- [Configuration Options](#-configuration-options)
- [Output Formats](#-output-formats)
- [Understanding Compliance Reports](#-understanding-compliance-reports)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [Development Status](#-development-status)
- [License](#-license)

## 🔍 Overview

The TNO AI Audit Document Scanner is a powerful local Python tool that:
- Scans folders of audit documents (PDFs, DOCX, XLSX)
- Uses a local LLM (Mistral or Llama2 via Ollama) to analyze content
- Checks for required information in documents (e.g., approvals, clauses, dates)
- Generates comprehensive audit readiness reports

This tool significantly reduces manual work in audit reviews and demonstrates how AI can effectively augment audit professionals.

## ✨ Features

- **Document Processing**
  - Multi-format support (PDF, DOCX, XLSX)
  - Automatic text extraction and normalization
  - Document classification by type

- **Compliance Modes**
  - **Static Mode**: Uses predefined checklists for validation
  - **Dynamic Mode**: Extracts requirements from policy documents
  - **Unified Workflow**: Intelligently selects appropriate mode

- **Analysis Capabilities**
  - LLM-powered document analysis
  - Confidence scoring for results
  - Comprehensive error handling

- **Output Options**
  - Multiple formats (JSON, CSV, HTML, Markdown, Excel)
  - Individual document validation
  - Cross-document compliance matrices

## 📁 Project Structure

```
TNO AI AUDIT DOCUMENT SCANNER/
├── src/                    # Source code
│   ├── document_loader.py  # Document loading and preprocessing
│   ├── document_classifier.py  # Document type classification 
│   ├── llm_wrapper.py     # LLM integration and prompt management
│   ├── policy_parser.py   # Policy requirement extraction
│   ├── compliance_evaluator.py  # Document compliance evaluation
│   ├── output_formatter.py  # Results formatting in multiple formats
│   ├── unified_workflow_manager.py  # Mode selection and integration
│   └── test_*.py          # Unit tests
├── docs/                   # Input documents for testing
├── outputs/                # Results (reports, summaries)
├── config/                 # Configuration files
│   ├── checklist.yaml     # Static audit checklist
│   └── policy_requirements.yaml  # Extracted requirements
├── PROJECT_BOARD.md        # Task board to track progress
└── README.md               # Project overview (this file)
```

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/tno-ai-audit-scanner.git
   cd tno-ai-audit-scanner
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Ollama:
   ```bash
   # Download and install Ollama from https://ollama.ai/
   
   # Download model (only needed once):
   ollama pull mistral
   # Or alternatively:
   ollama pull llama2
   ```

5. Verify installation:
   ```bash
   python -m src.test_llm_prompt
   ```

## 🚀 Quick Start Guide

Run a basic document scan with the default configuration:

```bash
python -m src.main --input-dir docs --output-dir outputs
```

This will:
1. Load documents from the `docs` directory
2. Extract requirements from any policy documents
3. Evaluate compliance of all other documents
4. Output results to the `outputs` directory

---

## 📚 Detailed Usage Guide

For comprehensive instructions on using the AI Audit Document Analyzer, please refer to our [Detailed Usage Guide](USAGE.md). The guide covers:

- Step-by-step installation and setup
- Detailed instructions for both static and dynamic modes
- Configuration file examples
- Common workflows and use cases
- Troubleshooting guide
- Quick reference tables
- Glossary of terms

## 📝 Usage Examples

### Static Mode Examples

Static mode uses a predefined checklist to validate documents against fixed criteria.

#### Running Static Mode Analysis

```bash
python -m src.main --input-dir docs --output-dir outputs --workflow-mode static
```

#### Example: Password Policy Validation

Let's validate a password policy document against predefined security criteria:

```bash
python -m src.main --input-dir docs/security_policies --output-dir outputs --workflow-mode static
```

##### [SCREENSHOT PLACEHOLDER: Static Mode Results]
*Caption: This screenshot shows the console output after running static mode validation on security policies. Notice the document list, processing status, and summary statistics at the bottom showing compliance percentages.*

*Key Elements:*
- *Console progress indicators*
- *Document classification results*
- *Processing status for each document*
- *Final compliance summary statistics*
- *Path to detailed report files*

*Recommended Dimensions: 1200x800px*

#### Static Mode Checklist Configuration

The static mode uses `config/checklist.yaml` to define validation criteria. Here's an example configuration:

```yaml
# Sample checklist.yaml structure
categories:
  - name: "Password Policy"
    items:
      - id: "password_length"
        name: "Password Length Requirement"
        description: "Document should specify minimum password length"
        required_keywords: ["minimum length", "at least", "characters long"]
        
      - id: "password_complexity"
        name: "Password Complexity Requirement"
        description: "Document should define password complexity requirements"
        required_keywords: ["uppercase", "lowercase", "numbers", "special characters"]
```

### Dynamic Mode Examples

Dynamic mode extracts requirements from policy documents and evaluates other documents against these extracted requirements.

#### Running Dynamic Mode Analysis

```bash
python -m src.main --input-dir docs --output-dir outputs --workflow-mode dynamic
```

#### Example: Extracting Requirements from a Master Policy

```bash
python -m src.policy_requirement_extractor --input-file docs/master_policy.pdf --output-file config/custom_requirements.yaml
```

##### [SCREENSHOT PLACEHOLDER: Policy Requirement Extraction]
*Caption: This screenshot displays the process of extracting compliance requirements from a master policy document. Notice how the system identifies and extracts structured requirements from unstructured text.*

*Key Elements:*
- *Input document information*
- *Extraction progress indicators*
- *List of identified requirements*
- *Category classification of requirements*
- *Confidence scores for extracted items*

*Recommended Dimensions: 1200x800px*

#### Evaluating Documents Against Extracted Requirements

```bash
python -m src.main --input-dir docs/audit_documents --output-dir outputs --workflow-mode dynamic
```

##### [SCREENSHOT PLACEHOLDER: Dynamic Mode Evaluation]
*Caption: This screenshot shows documents being evaluated against dynamically extracted requirements. The system maps each document to relevant requirements and provides compliance results.*

*Key Elements:*
- *Document-to-requirement mapping matrix*
- *Compliance levels (Fully/Partially/Non-Compliant)*
- *Confidence scores for each evaluation*
- *Evidence citations from documents*

*Recommended Dimensions: 1400x900px*

### Unified Workflow Examples

The unified workflow intelligently selects between static and dynamic modes based on document type and complexity.

#### Running Unified Workflow

```bash
python -m src.main --input-dir docs --output-dir outputs --workflow-mode unified
```

#### Example: Comprehensive Audit Preparation

```bash
# Process entire document repository with unified workflow
python -m src.main --input-dir docs/full_audit_set --output-dir outputs/audit_2025 --workflow-mode unified
```

##### [SCREENSHOT PLACEHOLDER: Unified Workflow Overview]
*Caption: This screenshot presents the unified workflow in action, showing automatic mode selection based on document type and complexity. Notice how different documents are processed with different modes for optimal results.*

*Key Elements:*
- *Mixed document set being processed*
- *Mode selection decisions for each document*
- *Processing flow from policy documents to audit documents*
- *Comprehensive matrix output*
- *Statistics on mode selection and effectiveness*

*Recommended Dimensions: 1600x1000px*

## ⚙️ Configuration Options

### Command-Line Options

The main application accepts various command-line options:

```
--input-dir PATH       Directory containing input documents (default: docs)
--output-dir PATH      Directory for output reports (default: outputs)
--config-dir PATH      Directory for configuration files (default: config)
--llm-model TEXT       LLM model to use for analysis (default: mistral)
--workflow-mode TEXT   Workflow mode to use (unified, static, or dynamic)
--log-level TEXT       Logging level (DEBUG, INFO, WARNING, ERROR)
```

### Configuration Files

The system uses several configuration files:

1. **checklist.yaml**: Defines static mode validation criteria
   ```yaml
   categories:
     - name: "Category Name"
       items:
         - id: "item_id"
           name: "Item Name"
           description: "Item Description"
           required_keywords: ["keyword1", "keyword2"]
   ```

2. **policy_requirements.yaml**: Stores extracted requirements
   ```yaml
   requirements:
     - id: "req_001"
       description: "Requirement description"
       category: "Security"
       type: "mandatory"
       priority: "high"
   ```

3. **workflow_config.yaml**: Controls workflow behavior
   ```yaml
   mode_preferences:
     policy: dynamic
     report: static
   confidence_threshold: 0.7
   max_retries: 3
   timeout_seconds: 300
   ```

## 📊 Output Formats

The system supports multiple output formats:

### JSON Format

```json
{
  "document_id": "password_policy.pdf",
  "document_name": "Corporate Password Policy",
  "document_type": "policy",
  "status": "passed",
  "metadata": {
    "timestamp": 1714503698.452729,
    "validator_version": "1.0.0",
    "mode": "dynamic",
    "confidence_score": 0.92,
    "processing_time_ms": 1243.5
  },
  "categories": [
    {
      "id": "password_requirements",
      "name": "Password Requirements",
      "status": "passed",
      "confidence_score": 0.95,
      "items": [
        {
          "id": "password_length",
          "name": "Password Length Requirement",
          "status": "passed",
          "confidence_score": 0.98,
          "details": {
            "justification": "Document specifies minimum 12 characters on page 3",
            "matched_keywords": ["minimum length", "12 characters"]
          }
        }
      ]
    }
  ]
}
```

##### [SCREENSHOT PLACEHOLDER: JSON Output Example]
*Caption: This screenshot shows a sample JSON output from the system, displayed in a code editor or viewer with syntax highlighting. This structured data format allows for programmatic processing of compliance results.*

*Key Elements:*
- *Full JSON structure with nested objects*
- *Document metadata section*
- *Categories and items hierarchy*
- *Status values and confidence scores*
- *Justification and evidence details*

*Recommended Dimensions: 1200x900px*

### HTML Reports

The system generates interactive HTML reports for easy viewing and sharing.

##### [SCREENSHOT PLACEHOLDER: HTML Report]
*Caption: This screenshot displays a professionally formatted HTML compliance report generated by the system. The report includes visual indicators of compliance status, detailed justifications, and summary statistics.*

*Key Elements:*
- *Header with document information*
- *Color-coded status indicators*
- *Category and requirement breakdown*
- *Compliance level visualizations*
- *Evidence and justification details*
- *Summary statistics section*

*Recommended Dimensions: 1400x1000px*

### Compliance Matrix

For multi-document evaluations, the system generates compliance matrices.

##### [SCREENSHOT PLACEHOLDER: Compliance Matrix]
*Caption: This screenshot shows a compliance matrix mapping multiple documents against multiple requirements. This view helps identify compliance gaps across the document set.*

*Key Elements:*
- *Requirements listed on vertical axis*
- *Documents listed on horizontal axis*
- *Color-coded compliance status in cells*
- *Filtering and sorting controls*
- *Summary statistics and dashboard elements*

*Recommended Dimensions: 1600x900px*

## 🔍 Understanding Compliance Reports

### Compliance Levels

The system uses the following compliance levels:

| Level | Symbol | Meaning |
|-------|--------|---------|
| Fully Compliant | ✅ | Document completely satisfies requirements |
| Partially Compliant | ⚠️ | Document addresses some aspects but not all |
| Non-Compliant | ❌ | Document fails to meet requirements |
| Not Applicable | ➖ | Requirement doesn't apply to this document |
| Indeterminate | ❓ | System couldn't determine compliance status |

### Confidence Scores

Confidence scores (0.0-1.0) indicate the system's certainty in its assessment:
- **0.9-1.0**: High confidence, very reliable
- **0.7-0.9**: Good confidence, generally reliable
- **0.5-0.7**: Moderate confidence, may need human review
- **0.0-0.5**: Low confidence, requires human validation

##### [SCREENSHOT PLACEHOLDER: Understanding Report Elements]
*Caption: This annotated screenshot explains how to interpret different elements of compliance reports. It highlights key visual indicators, score interpretations, and how to identify areas needing attention.*

*Key Elements:*
- *Annotated report sections with explanatory callouts*
- *Legend for status indicators and colors*
- *Confidence score interpretation guide*
- *Examples of fully compliant vs. non-compliant items*
- *Tips for identifying priority issues*

*Recommended Dimensions: 1400x1000px*

## ❓ Troubleshooting & FAQ

### Common Issues

#### LLM Connection Issues

**Problem**: `ConnectionError: Failed to connect to Ollama server`

**Solution**:
1. Ensure Ollama is installed and running
2. Verify the model is downloaded: `ollama list`
3. Check for network issues if using a remote Ollama instance

#### Document Processing Errors

**Problem**: `Document extraction failed for file.pdf`

**Solution**:
1. Verify the file isn't corrupted or password-protected
2. Check if the file is readable by standard PDF libraries
3. Try converting the file to a different format

#### Low Confidence Results

**Problem**: Many results have low confidence scores

**Solution**:
1. Improve your policy documents with clearer language
2. Adjust confidence thresholds in configuration
3. Review and validate results manually

### FAQ

**Q: How does the system decide between static and dynamic modes?**

A: The unified workflow selects modes based on:
- Document type (policies use dynamic mode)
- Document complexity (complex documents use dynamic mode)
- User configuration preferences
- Processing history and performance

**Q: Can I customize the validation criteria?**

A: Yes, you can:
- Edit `checklist.yaml` for static mode criteria
- Create custom policy documents for dynamic extraction
- Adjust confidence thresholds and matching parameters

**Q: How can I improve accuracy?**

A: To improve accuracy:
- Use higher-quality LLM models (e.g., Llama-2-13B instead of 7B)
- Provide clearer policy documents for requirement extraction
- Adjust confidence thresholds to match your needs
- Add domain-specific terminology to the checklist

## 🗓️ Development Status

**Current Phase:** Week 5 - Polish & Delivery
- ✅ Document handling and preprocessing
- ✅ LLM integration and prompt management
- ✅ Error handling and response scoring
- ✅ Static mode implementation
- ✅ Dynamic mode implementation
- ✅ Unified workflow integration
- ✅ Multiple output format support

## 📝 License

This software is proprietary and confidential. All rights reserved. Unauthorized use, reproduction, or distribution of this software is strictly prohibited. For licensing inquiries, please contact TNO.