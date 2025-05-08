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
- [x] Finalize static checklist validation loop
- [x] Prepare static mode for integration with dynamic mode (unified interface/data structure)
- [x] Define consistent output format for both static and dynamic modes


---

## 🧠 Week 4: Policy-Driven Audit Analysis (Dynamic Mode)

- [x] Build `policy_parser.py` to extract compliance requirements from a policy document using LLM
- [x] Prompt LLM: "List all audit/compliance requirements from this document"
- [x] Store extracted checklist dynamically (in memory or `/config/policy_requirements.yaml`)
- [x] Feed audit documents + extracted rules into compliance evaluator
- [x] Prompt LLM: "Does this doc satisfy requirement X? Y/N and explain"
- [x] Generate full compliance matrix as output report
- [x] Compare results of static vs. dynamic modes
- [x] Integrate static and dynamic modes into a unified workflow
- [x] Handle edge cases (e.g., LLM extraction failures, unmatched documents)
- [x] Test dynamic mode with real/simulated documents
- [x] Define and implement output format for compliance matrix (e.g., JSON, CSV, visual report)

---

## 📈 Week 5: Polish & Delivery

- [x] Finalize both static and policy-based compliance modes
- [x] Add examples and screenshots to `README.md`
- [ ] Write clear usage guide (running static and policy modes)
- [ ] Prepare for User Acceptance Testing
  - [ ] Create test document set (2-3 policy documents, 3-5 audit documents)
  - [ ] Prepare expected compliance results for validation
  - [ ] Set up testing checklist with pass/fail criteria
- [ ] Conduct User Acceptance Testing
  - [ ] Test 1: Fresh installation following only README instructions
  - [ ] Test 2: Document processing using static checklist mode
  - [ ] Test 3: Policy requirement extraction using dynamic mode
  - [ ] Test 4: Compliance evaluation of audit documents
  - [ ] Test 5: Generating and reviewing compliance reports
  - [ ] Test 6: Error handling with incorrect inputs
  - [ ] Document all test results including screenshots
- [ ] User Experience Evaluation
  - [ ] Evaluate clarity of command interface
  - [ ] Assess report readability and usefulness
  - [ ] Measure time required for key operations
  - [ ] Identify any confusing steps or unclear instructions
- [ ] Optimize based on testing results
  - [ ] Address issues discovered during testing
  - [ ] Improve user instructions for complex steps
  - [ ] Optimize prompt speed and chunking
  - [ ] Enhance error messages for clarity
- [ ] Prepare presentation or walkthrough (optional for TNO)
- [ ] ✅ Done = Celebrate 🎉

## 🔄 Ongoing

- [ ] Log blockers and learning insights as Markdown checklist
- [ ] Track future ideas (e.g. embedding-based search, dynamic UI, anomaly detection)
- [ ] Review and reprioritize board at least weekly

## Core Features
- [x] Implement static mode document processing
- [x] Implement dynamic mode document processing
- [x] Create unified workflow manager
- [x] Handle edge cases (e.g., LLM extraction failures, unmatched documents)

## Integration Tasks
- [ ] Integrate with external compliance databases
- [ ] Implement real-time monitoring and alerts
- [ ] Add support for custom compliance rules

## Testing & Quality Assurance
- [x] Create comprehensive test suite
- [x] Implement performance benchmarking
- [ ] Add automated regression testing

## Documentation & Maintenance
- [ ] Create user documentation
- [ ] Document API endpoints
- [ ] Set up automated deployment pipeline
