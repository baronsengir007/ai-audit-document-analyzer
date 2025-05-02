# 📊 Project Board: AI Audit Document Analyzer

## 📅 Week 1: Setup & Project Kickoff

- [x] Install Python 3.10+ and set up a virtual environment
- [x] Install base libraries: `PyPDF2`, `python-docx`, `openpyxl`, `pandas`
- [x] Install and run Ollama + download a model (Mistral-7B or Llama2-7B)
- [x] Test sending prompt to LLM from Python (e.g., "Summarize this audit doc.")
- [x] Create folder structure (`docs`, `outputs`, `scripts`, `config`)
- [x] Push initial project to GitHub
- [x] Write `README.md` (project vision, structure, timeline)

---

## 🧾 Week 2: Document Handling

- [x] Implement PDF text extraction
- [x] Implement Word and Excel text extraction
- [x] Normalize extracted content into one format (e.g., plain text with metadata)
- [x] Create mock document samples in `/docs/`
- [x] Define checklist format for static audit completeness (`/config/checklist.yaml`)


---

## 🧠 Week 3: LLM Integration (Static Checklist Mode)

- [x] Build document classifier to sort by type
- [x] Build checklist validator (static rule-based)
  - [x] Read `normalized_docs.json` and `checklist.yaml`
  - [x] Match classified document types to checklist categories
  - [x] For each category, scan for required keywords in content
  - [x] Report results: ✓ complete / ✗ missing (per checklist item)
- [x] Create Python wrapper for Ollama local LLM (for both static and dynamic modes)
- [x] Develop prompt templates for static checklist analysis
  - [x] Completeness check
  - [x] Required fields verification
- [x] Parse LLM responses into structured JSON output
- [x] Add error handling and response scoring
- [ ] Finalize static checklist validation loop
- [ ] Prepare static mode for integration with dynamic mode (unified interface/data structure)
- [ ] Define consistent output format for both static and dynamic modes


---

## 🧠 Week 4: Policy-Driven Audit Analysis (Dynamic Mode)

- [ ] Build `policy_parser.py` to extract compliance requirements from a policy document using LLM
- [ ] Prompt LLM: "List all audit/compliance requirements from this document"
- [ ] Store extracted checklist dynamically (in memory or `/config/policy_requirements.yaml`)
- [ ] Feed audit documents + extracted rules into compliance evaluator
- [ ] Prompt LLM: "Does this doc satisfy requirement X? Y/N and explain"
- [ ] Generate full compliance matrix as output report
- [ ] Compare results of static vs. dynamic modes
- [ ] Integrate static and dynamic modes into a unified workflow
- [ ] Handle edge cases (e.g., LLM extraction failures, unmatched documents)
- [ ] Test dynamic mode with real/simulated documents
- [ ] Define and implement output format for compliance matrix (e.g., JSON, CSV, visual report)

---

## 📈 Week 5: Polish & Delivery

- [ ] Finalize both static and policy-based compliance modes
- [ ] Add examples and screenshots to `README.md`
- [ ] Write clear usage guide (running static and policy modes)
- [ ] Full run-through test on 3-5 real/simulated documents
- [ ] Optimize prompt speed, chunking, and UX
- [ ] Prepare presentation or walkthrough (optional for TNO)
- [ ] ✅ Done = Celebrate 🎉

---

## 🔄 Ongoing

- [ ] Log blockers and learning insights as Markdown checklist
- [ ] Track future ideas (e.g. embedding-based search, dynamic UI, anomaly detection)
- [ ] Review and reprioritize board at least weekly
