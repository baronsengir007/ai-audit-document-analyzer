# 🧠 TNO AI Audit Document Scanner

## 🔍 Project Goal

Build a local Python tool that:
- Scans folders of audit documents (PDFs, DOCX, XLSX)
- Uses a local LLM (Mistral or Llama2 via Ollama) to analyze content
- Checks for required information in documents (e.g., approvals, clauses, dates)
- Generates a clear audit readiness report

This tool reduces manual work in audit reviews and demonstrates how AI can be used to augment professionals.

---

## 📁 Project Structure

```
TNO AI AUDIT DOCUMENT SCANNER/
├── src/                    # Source code
│   ├── document_loader.py  # Document loading and preprocessing
│   ├── document_classifier.py  # Document type classification
│   ├── llm_wrapper.py     # LLM integration and prompt management
│   ├── llm_error_handler.py  # Error handling and recovery
│   ├── llm_response_scorer.py  # Response quality assessment
│   ├── json_parser.py     # JSON response parsing and validation
│   ├── checklist_validator.py  # Static checklist validation
│   └── test_*.py          # Unit tests
├── docs/                   # Input documents for testing
├── outputs/               # Results (reports, summaries)
├── config/                # Configuration files
│   └── checklist.yaml     # Static audit checklist
├── PROJECT_BOARD.md       # Task board to track progress
└── README.md              # Project overview (this file)
```

---

## ⚙️ Tech Stack

- Python 3.10+
- Local LLM (Ollama + Mistral-7B or Llama-2-7B)
- Core Libraries:
  - PyPDF2 (PDF extraction)
  - python-docx (Word)
  - openpyxl (Excel)
  - backoff (retry mechanisms)
  - jsonschema (JSON validation)
- Development Tools:
  - pytest (testing)
  - black (code formatting)
  - flake8 (linting)
  - mypy (type checking)

---

## 🚀 Current Progress

### ✅ Completed Features
- Document loading and preprocessing
- Document type classification
- LLM integration with Ollama
- Prompt template management
- JSON response parsing
- Comprehensive error handling
- Response quality scoring
- Static checklist validation

### 🚧 In Progress
- Finalizing static checklist validation loop
- Preparing for dynamic mode integration
- Defining unified output format

---

## 📄 Example Output

The system generates structured JSON reports with:
- Document analysis results
- Checklist compliance status
- Confidence scores
- Error handling details
- Quality metrics

Example output structure:
```json
{
  "document_id": "invoice_2023.pdf",
  "analysis": {
    "completeness": 0.95,
    "required_fields": ["date", "amount", "approval"],
    "missing_fields": [],
    "confidence_score": 0.92
  },
  "metadata": {
    "processing_time": "0.5s",
    "error_count": 0,
    "warnings": []
  }
}
```

---

## 🛠️ Development Setup

1. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Ollama:
   ```bash
   # Install Ollama
   # Download model: ollama pull mistral
   ```

4. Run tests:
   ```bash
   pytest src/
   ```

---

## 🗓️ Timeline

**Current Phase:** Week 3 - LLM Integration (Static Checklist Mode)
- ✅ Document handling and preprocessing
- ✅ LLM integration and prompt management
- ✅ Error handling and response scoring
- 🚧 Finalizing static mode
- 📅 Next: Dynamic mode implementation

---

## 📝 License

This software is proprietary and confidential. All rights reserved. Unauthorized use, reproduction, or distribution of this software is strictly prohibited. For licensing inquiries, please contact TNO.
