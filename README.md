# 🧠 TNO AI Audit Document Scanner

## 🔍 Project Goal

Build a local Python tool that:
- Scans folders of audit documents (PDFs, DOCX, XLSX)
- Uses a local LLM (Mistral or Llama2 via Ollama) to analyze content
- Checks for required information in documents (e.g., approvals, clauses, dates)
- Generates a clear audit readiness report

This tool reduces manual work in audit reviews and demonstrates how AI can be used to augment professionals.

---

## 📁 Folder Structure

```
TNO AI AUDIT DOCUMENT SCANNER/
├── main.py              # Entry point
├── scripts/             # Python logic (document reader, AI interface)
├── docs/                # Input documents for testing
├── outputs/             # Results (reports, summaries)
├── config/              # Document checklists, AI prompt configs
├── PROJECT_BOARD.md     # Task board to track progress
└── README.md            # Project overview (this file)
```

---

## ⚙️ Tech Stack

- Python 3.10+
- Local LLM (Ollama + Mistral-7B or Llama-2-7B)
- Libraries:
  - PyPDF2 (PDF extraction)
  - python-docx (Word)
  - openpyxl (Excel)
  - pandas (dataframes)
- Optional:
  - Streamlit (UI)

---

## 📄 Example Output

Imagine you drop three audit docs into the tool:

- ✅ `invoice_2023.pdf` → All checks passed
- ❌ `contract.docx` → Missing approval signature
- ✅ `summary.xlsx` → Budget fields found

The tool would generate a report like this and export it to `/outputs`.

---

## 🚀 Long-Term Vision

This is the foundation for:
- AI-enhanced audit workflows
- Tools you can bring to TNO and beyond
- A future consulting practice around AI adoption in compliance

---

## 🗓️ Timeline

**Working prototype deadline:**  
May 2025 (5-week development sprint)
