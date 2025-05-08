# 📖 AI Audit Document Analyzer Usage Guide

## 📋 Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Basic Setup](#basic-setup)
4. [Static Checklist Mode](#static-checklist-mode)
5. [Dynamic Policy Mode](#dynamic-policy-mode)
6. [Understanding Results](#understanding-results)
7. [Troubleshooting](#troubleshooting)
8. [Quick Reference](#quick-reference)
9. [Glossary](#glossary)

## Introduction

The AI Audit Document Analyzer helps you validate audit documents against compliance requirements using two powerful modes:
- **Static Checklist Mode**: Validates documents against predefined checklists
- **Dynamic Policy Mode**: Extracts requirements from policy documents and validates other documents against them

### Prerequisites
- Python 3.10 or higher
- Ollama installed with either Mistral or Llama2 model
- Basic understanding of command-line interfaces
- PDF, DOCX, and XLSX documents to analyze

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/ai-audit-document-analyzer.git
   cd ai-audit-document-analyzer
   ```

2. **Set Up Virtual Environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ollama**
   - Download from [ollama.ai](https://ollama.ai)
   - Install following platform-specific instructions
   - Download model:
     ```bash
     ollama pull mistral  # or
     ollama pull llama2
     ```

## Basic Setup

1. **Directory Structure**
   ```
   ai-audit-document-analyzer/
   ├── docs/           # Place your documents here
   ├── outputs/        # Results will be saved here
   └── config/         # Configuration files
   ```

2. **Configuration Files**
   - `config/checklist.yaml`: Static mode checklist
   - `config/workflow_config.yaml`: General settings

## Static Checklist Mode

### Basic Usage
```bash
python -m src.main --input-dir docs --output-dir outputs --workflow-mode static
```

### Example: Validating Security Policies
```bash
python -m src.main \
  --input-dir docs/security_policies \
  --output-dir outputs \
  --workflow-mode static \
  --checklist config/security_checklist.yaml
```

### Checklist Configuration
```yaml
# config/checklist.yaml
categories:
  - name: "Password Policy"
    items:
      - id: "password_length"
        name: "Minimum Length"
        required_keywords: ["minimum length", "at least"]
      - id: "password_complexity"
        name: "Complexity Requirements"
        required_keywords: ["uppercase", "lowercase", "numbers"]
```

## Dynamic Policy Mode

### Basic Usage
```bash
python -m src.main --input-dir docs --output-dir outputs --workflow-mode dynamic
```

### Example: Policy-Based Analysis
```bash
# Step 1: Extract requirements from policy
python -m src.policy_requirement_extractor \
  --input-file docs/master_policy.pdf \
  --output-file config/policy_requirements.yaml

# Step 2: Validate documents against requirements
python -m src.main \
  --input-dir docs/audit_documents \
  --output-dir outputs \
  --workflow-mode dynamic \
  --requirements config/policy_requirements.yaml
```

## Understanding Results

### Output Formats
- **JSON**: Detailed structured data
- **CSV**: Tabular format for spreadsheet analysis
- **HTML**: Interactive web report
- **Markdown**: Documentation-friendly format

### Example JSON Output
```json
{
  "document": "password_policy.pdf",
  "compliance_score": 0.85,
  "requirements": [
    {
      "id": "password_length",
      "status": "compliant",
      "evidence": "Minimum password length must be 12 characters"
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **Ollama Connection Error**
   ```bash
   Error: Could not connect to Ollama
   Solution: Ensure Ollama is running (ollama serve)
   ```

2. **Document Processing Error**
   ```bash
   Error: Failed to process document.pdf
   Solution: Check file permissions and format
   ```

3. **Configuration Error**
   ```bash
   Error: Invalid checklist format
   Solution: Validate YAML syntax in config files
   ```

## Quick Reference

### Command-Line Options
| Option | Description | Example |
|--------|-------------|---------|
| `--input-dir` | Input documents directory | `--input-dir docs` |
| `--output-dir` | Results output directory | `--output-dir outputs` |
| `--workflow-mode` | Analysis mode | `--workflow-mode static` |
| `--checklist` | Checklist file | `--checklist config/checklist.yaml` |

### Common Workflows

1. **Quick Document Check**
   ```bash
   python -m src.main --input-dir docs --output-dir outputs
   ```

2. **Policy Requirement Extraction**
   ```bash
   python -m src.policy_requirement_extractor --input-file policy.pdf
   ```

3. **Batch Processing**
   ```bash
   python -m src.main --input-dir docs --output-dir outputs --batch-size 10
   ```

## Glossary

- **Static Mode**: Predefined checklist-based validation
- **Dynamic Mode**: Policy-based requirement extraction and validation
- **Compliance Score**: Percentage of requirements met (0-1)
- **Evidence**: Text snippets supporting compliance decisions
- **Requirements**: Compliance criteria extracted from policies

---

*Note: This guide is for version 1.0.0. Check the repository for updates.* 