# TNO AI Audit Document Scanner - Foundation Prompt

## Project Overview

The TNO AI Document Classification System is a specialized tool designed for semantic classification of organizational documents. Unlike simpler keyword-matching approaches, this system leverages AI to understand document meaning and purpose, helping organizations ensure they have all required document types based on semantic content.

### Core Capabilities

- Semantically classifies documents (PDFs, DOCX, XLSX) into predefined types
- Uses local LLM (Mistral or Llama2 via Ollama) for semantic understanding
- Verifies if all required document types are present in a document collection
- Provides confidence scores and evidence for classifications
- Generates clear HTML and JSON reports on document coverage

## Current Architecture

The system follows a clear pipeline architecture with these primary components:

1. **Document Processing**: Handles document loading and text extraction
   - `document_processor.py`: Multi-format support (PDF, DOCX, XLSX) with robust error handling
   - Uses PyPDF2, python-docx, and openpyxl for extraction
   - Standardizes document representation with metadata

2. **Semantic Classification**: AI-powered document classification
   - `semantic_classifier.py`: Core classification using LLM
   - `llm_wrapper.py`: Interface to Ollama local LLM API
   - Configuration-driven document type definitions
   - Evidence extraction and confidence scoring

3. **Type Verification**: Requirements satisfaction checking
   - `type_verification.py`: Verifies document types against requirements
   - Identifies missing required documents
   - Calculates coverage metrics

4. **Results Visualization**: Reporting and presentation
   - `results_visualizer.py`: Generates HTML and JSON reports
   - Interactive dashboard with coverage metrics
   - Detailed document evidence display

5. **Main Pipeline**: Orchestration and workflow
   - `main.py`: Coordinates the complete classification process
   - Command-line interface with configuration options
   - Caching for performance optimization

### Project Structure

```
TNO AI DOCUMENT CLASSIFICATION/
├── src/                    # Source code
│   ├── document_processor.py  # Document loading and text extraction
│   ├── semantic_classifier.py # LLM-based semantic classification
│   ├── type_verification.py   # Document type verification
│   ├── results_visualizer.py  # Report generation
│   ├── llm_wrapper.py         # LLM integration
│   ├── main.py                # Application entry point
│   └── test_*.py              # Unit tests
├── docs/                   # Input documents for testing
├── outputs/                # Results (reports, summaries)
├── config/                 # Configuration files
│   └── document_types.yaml # Document type definitions
├── test_results/           # Test execution results
└── README.md               # Project overview
```

## Development Status

The project has been developed in phases, with a strong emphasis on test-driven development:

### Completed Phases

1. **Phase 1: Clean-up & Foundation** ✅
   - Project backup
   - Removal of obsolete components
   - Document types configuration
   - Main.py simplification

2. **Phase 2: Core Classifier System** ✅
   - Implementation of semantic classifier
   - Document type verification
   - Results visualization
   - Unit tests for new components

3. **Phase 3: Integration & Refactoring** ✅
   - Refactoring document processor
   - Updating LLM prompts
   - Completing main pipeline
   - Component integration

### Current Phase

4. **Phase 4: Testing & Reporting** 🔄 (In Progress)
   - Creating test document set
   - Implementing end-to-end test
   - Generating test reports
   - Documenting test results

### Planned Phase

5. **Phase 5: Optional Enhancements** 📅 (Planned)
   - Enhancing prompt engineering
   - Improving confidence scoring
   - Supporting hierarchical document types
   - Implementing human review interface

## Technical Specifications

### Language and Frameworks

- **Python 3.10+**: Core implementation language
- **Testing**: pytest for unit testing
- **Documentation**: Markdown for documentation

### Key Dependencies

- **Document Processing**:
  - PyPDF2: PDF text extraction
  - python-docx: Word document processing
  - openpyxl: Excel document processing

- **AI/ML**:
  - Ollama: Local LLM hosting
  - Mistral-7B or Llama2-7B: Base models

- **Configuration**:
  - PyYAML: Configuration file handling

### System Requirements

- Python 3.10 or newer
- 16GB+ RAM recommended for LLM operation
- Ollama installed locally
- At least one LLM model downloaded (Mistral-7B or Llama2-7B)

## Coding Standards and Patterns

### Code Style

- PEP 8 compliant
- Type hints for function parameters and return values
- Comprehensive docstrings in Google style
- Modular design with clear separation of concerns

### Design Patterns

1. **Pipeline Processing**: Sequential document processing stages
2. **Strategy Pattern**: Pluggable classification strategies
3. **Factory Method**: For document and report creation
4. **Adapter Pattern**: For various document format handling
5. **Decorator Pattern**: For logging and timing operations

### Error Handling

- Robust error handling with graceful degradation
- Comprehensive logging with different verbosity levels
- Fallback mechanisms for extraction failures

### Testing Policy

- All code must have corresponding unit tests
- Integration tests to verify component interactions
- Test validation using `verify_tests.sh` script
- No task or component marked complete without passing tests
- Test results documented in the `/test_results` folder

## Configuration

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
```

### Command-Line Interface

The main application accepts various command-line options:

```
--input-dir PATH       Directory containing input documents (default: docs)
--output-dir PATH      Directory for output reports (default: outputs)
--config-dir PATH      Directory for configuration files (default: config)
--llm-model TEXT       LLM model to use for analysis (default: mistral)
--confidence-threshold VALUE  Minimum confidence score (default: 0.7)
--log-level TEXT       Logging level (DEBUG, INFO, WARNING, ERROR)
```

## Development Roadmap

### Short-term Goals

1. Complete Phase 4: Testing & Reporting
   - Implement end-to-end test scripts
   - Create comprehensive test document set
   - Generate and validate test reports

2. Begin Phase 5: Optional Enhancements
   - Research improved prompt engineering techniques
   - Develop confidence calibration methods
   - Design hierarchical document type system

### Long-term Vision

1. **Advanced Classification**
   - Implement hierarchical document classification
   - Support for cross-referencing between documents
   - Integration with external knowledge bases

2. **User Interface Improvements**
   - Web-based dashboard for results visualization
   - Document upload and management interface
   - Interactive report filtering and search

3. **Performance Optimization**
   - Parallel processing for large document sets
   - Incremental processing for document updates
   - Optimized LLM prompts for faster inference

## Getting Started for Development

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

7. Run a basic document classification:
   ```bash
   python -m src.main --input-dir docs --output-dir outputs
   ```

## Critical Development Guidelines

1. **Test First**: Always write tests before implementing new features
2. **Verification**: Run `verify_tests.sh` after any significant change
3. **Documentation**: Update documentation as code evolves
4. **Error Handling**: Ensure robust error handling in all components
5. **Semantic Focus**: Maintain focus on semantic understanding, not just keyword matching
6. **Performance**: Monitor and optimize LLM operations for performance
7. **Configurability**: Make new features configurable when possible

## License and Ownership

This software is proprietary and confidential. All rights reserved by TNO. Unauthorized use, reproduction, or distribution of this software is strictly prohibited.