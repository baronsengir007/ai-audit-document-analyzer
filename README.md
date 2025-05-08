# 🧠 TNO AI Document Classification System

## 📋 Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Quick Start Guide](#-quick-start-guide)
- [Usage Examples](#-usage-examples)
- [Configuration](#-configuration)
- [Output Formats](#-output-formats)
- [Development Status](#-development-status)
- [License](#-license)

## 🔍 Overview

The TNO AI Document Classification System is a specialized tool that:
- Semantically classifies documents (PDFs, DOCX, XLSX) into predefined types
- Uses a local LLM (Mistral or Llama2 via Ollama) for semantic understanding
- Verifies if all required document types are present in a collection
- Provides confidence scores and evidence for classifications
- Generates clear reports on document coverage

This tool goes beyond simple keyword matching by using AI to understand document meaning and purpose, helping organizations ensure they have all required document types based on semantic content.

## ✨ Features

- **Document Processing**
  - Multi-format support (PDF, DOCX, XLSX)
  - Automatic text extraction and normalization
  - Document metadata analysis

- **Semantic Classification**
  - LLM-powered document type classification
  - Confidence scoring for classifications
  - Evidence extraction and citation
  - Required document type verification

- **Output Options**
  - Multiple formats (JSON, HTML, CSV)
  - Classification evidence reports
  - Document type coverage analysis

## 📁 Project Structure

```
TNO AI DOCUMENT CLASSIFICATION/
├── src/                    # Source code
│   ├── document_loader.py  # Document loading and preprocessing
│   ├── document_processor.py  # Text extraction and normalization
│   ├── pdf_extractor.py    # PDF handling utilities
│   ├── document_classifier.py  # Basic document classification
│   ├── semantic_classifier.py  # LLM-based semantic classification
│   ├── type_verification.py  # Document type verification
│   ├── results_visualizer.py  # Report generation
│   ├── llm_wrapper.py     # LLM integration and prompt management
│   ├── main.py            # Main application entry point
│   └── test_*.py          # Unit tests
├── docs/                   # Input documents for testing
├── outputs/                # Results (reports, summaries)
├── config/                 # Configuration files
│   └── document_types.yaml  # Document type definitions
├── PROJECT_BOARD.md        # Task board to track progress
└── README.md               # Project overview (this file)
```

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/tno-document-classifier.git
   cd tno-document-classifier
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

6. Validate all tests:
   ```bash
   ./verify_tests.sh
   ```

   > 🔐 **Important**: All test results must be validated using ./verify_tests.sh.
   > No task or phase may be marked complete unless this script exits successfully.

## 🚀 Quick Start Guide

### Testing and Validation

Before using the system, ensure all tests pass:

```bash
./verify_tests.sh
```

This script will run all tests and verify they pass without errors or warnings. Only proceed if the script exits successfully with the message: `✅ All tests passed successfully. No warnings or errors detected.`

Run a basic document classification with the default configuration:

```bash
python -m src.main --input-dir docs --output-dir outputs
```

This will:
1. Load documents from the `docs` directory
2. Classify each document using semantic understanding
3. Verify which required document types are present/missing
4. Output classification results to the `outputs` directory

## 📝 Usage Examples

### Basic Document Classification

```bash
python -m src.main --input-dir docs --output-dir outputs
```

This performs semantic classification on all documents in the input directory.

### Getting Classification Results

After running the classification, you'll find several output files:

- `classification_report.html` - Interactive HTML report of document types
- `classification_results.json` - Structured data with all classifications
- `pipeline_summary.json` - Overall summary of processing results

### Example Output

The system clearly shows which document types were found and which are missing:

```
Summary:
Documents processed: 12
Document types found: 5 of 8
Coverage: 62.5%

Missing document types:
 - incident_response_plan
 - acceptable_use_policy
 - data_retention_policy

HTML report: outputs/classification_report.html
```

## ⚙️ Configuration

### Command-Line Options

The main application accepts various command-line options:

```
--input-dir PATH       Directory containing input documents (default: docs)
--output-dir PATH      Directory for output reports (default: outputs)
--config-dir PATH      Directory for configuration files (default: config)
--llm-model TEXT       LLM model to use for analysis (default: mistral)
--confidence-threshold VALUE  Minimum confidence score (default: 0.7)
--log-level TEXT       Logging level (DEBUG, INFO, WARNING, ERROR)
```

### Document Types Configuration

The system uses `document_types.yaml` to define document types:

```yaml
document_types:
  - id: privacy_policy
    name: "Privacy Policy"
    description: "Document explaining how user data is collected, used, and protected"
    required: true
    examples:
      - "We collect the following types of personal information..."
      - "Your data is processed according to the following principles..."
      
  - id: data_processing_agreement
    name: "Data Processing Agreement (DPA)"
    description: "Legal contract between data controller and processor regarding personal data"
    required: true
    examples:
      - "The Processor shall process the Personal Data only on documented instructions..."
```

You can customize this file to define the document types relevant to your organization.

## 📊 Output Formats

### HTML Report

The system generates an interactive HTML report showing:
- Overall document type coverage
- Which document types were found/missing
- Document details and classification confidence
- Evidence that supports each classification

### JSON Format

```json
{
  "verification": {
    "coverage_percentage": 62.5,
    "required_types_count": 8,
    "found_required_types_count": 5,
    "missing_types": [
      {"id": "incident_response_plan"},
      {"id": "acceptable_use_policy"},
      {"id": "data_retention_policy"}
    ],
    "all_types": {
      "privacy_policy": {
        "name": "Privacy Policy",
        "documents": [
          {
            "document_id": "privacy_policy_v2.pdf",
            "confidence": 0.95,
            "evidence": ["personal data", "data processing", "user privacy"]
          }
        ],
        "found": true,
        "required": true
      }
      // Additional types...
    }
  },
  "classifications": [
    {
      "document_id": "privacy_policy_v2.pdf",
      "classified_type": "privacy_policy",
      "confidence": 0.95,
      "rationale": "This document clearly outlines how personal data is collected, processed, and protected. It includes sections on user rights, data retention, and privacy principles.",
      "evidence": ["personal data", "data processing", "user privacy"]
    }
    // Additional classifications...
  ]
}
```

## 🗓️ Development Status

The project is being developed in phases:

1. **Clean-up & Foundation**: ✅ Complete
   - Project backup
   - Removal of obsolete components
   - Document types configuration
   - Main.py simplification

2. **Core Classifier System**: 🔄 In Progress
   - Implementing semantic classifier
   - Document type verification
   - Results visualization

3. **Integration & Refactoring**: 📅 Planned
   - Refactoring document processor
   - Updating LLM prompts
   - Completing main pipeline

4. **Testing & Reporting**: 📅 Planned
   - Creating test document set
   - Implementing end-to-end testing
   - Generating test reports

5. **Optional Enhancements**: 📅 Planned
   - Enhancing prompt engineering
   - Improving confidence scoring
   - Supporting hierarchical document types

## 📝 License

This software is proprietary and confidential. All rights reserved. Unauthorized use, reproduction, or distribution of this software is strictly prohibited. For licensing inquiries, please contact TNO.