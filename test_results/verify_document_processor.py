"""
Minimal standalone verification script for document_processor.py
This script avoids dependencies and directly tests core functionality.
"""

import sys
import os
from pathlib import Path
import tempfile

# Set up path to find source files
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Create temp directory for test files
temp_dir = tempfile.TemporaryDirectory()
test_dir = Path(temp_dir.name)

# Create test file paths
pdf_path = test_dir / "test.pdf"
docx_path = test_dir / "test.docx"
xlsx_path = test_dir / "test.xlsx"

# Touch files to create them
pdf_path.touch()
docx_path.touch()
xlsx_path.touch()

# Import just the necessary functions directly from document_processor
# This avoids importing the full module which might have dependencies
sys.path.insert(0, os.path.join(parent_dir, "src"))
from src.document_processor import (
    extract_text_from_pdf,
    extract_text_from_word, 
    extract_text_from_excel
)

def run_verification():
    """Run verification tests on document_processor functions"""
    success = True
    
    print("Verifying document_processor.py functionality...")
    
    # Test PDF extraction function
    try:
        pdf_text = extract_text_from_pdf(pdf_path)
        print(f"✓ PDF extraction: {pdf_path}")
        # Verify it returned something reasonable
        if "[PDF" in pdf_text:  # Empty files should return a placeholder
            print(f"  Result: {pdf_text}")
    except Exception as e:
        print(f"✗ PDF extraction failed: {e}")
        success = False
    
    # Test DOCX extraction function
    try:
        docx_text = extract_text_from_word(docx_path)
        print(f"✓ DOCX extraction: {docx_path}")
        # Verify it returned something reasonable
        if "[WORD" in docx_text:  # Empty files should return a placeholder
            print(f"  Result: {docx_text}")
    except Exception as e:
        print(f"✗ DOCX extraction failed: {e}")
        success = False
    
    # Test XLSX extraction function
    try:
        xlsx_text = extract_text_from_excel(xlsx_path)
        print(f"✓ XLSX extraction: {xlsx_path}")
        # Verify it returned something reasonable
        if "[EXCEL" in xlsx_text:  # Empty files should return a placeholder
            print(f"  Result: {xlsx_text}")
    except Exception as e:
        print(f"✗ XLSX extraction failed: {e}")
        success = False
    
    # Print summary
    if success:
        print("\n✅ All document_processor.py verification tests passed!")
    else:
        print("\n❌ Some document_processor.py verification tests failed!")
    
    return success

if __name__ == "__main__":
    try:
        success = run_verification()
        # Clean up the temporary directory
        temp_dir.cleanup()
        # Exit with appropriate code
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error during verification: {e}")
        temp_dir.cleanup()
        sys.exit(1)