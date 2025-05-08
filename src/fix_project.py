import os
import sys
from pathlib import Path
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_filename(filename: str) -> str:
    """Normalize filename to follow our convention."""
    # Convert to lowercase
    normalized = filename.lower()
    
    # Replace spaces with underscores
    normalized = normalized.replace(' ', '_')
    
    # Remove any other invalid characters
    normalized = ''.join(c for c in normalized if c.isalnum() or c in '._-')
    
    return normalized

def rename_files(directory: str):
    """Rename files in the given directory according to our naming convention."""
    dir_path = Path(directory)
    if not dir_path.exists():
        logger.error(f"Directory not found: {directory}")
        return
    
    # Process all files in the directory
    for file_path in dir_path.glob('*'):
        if file_path.is_file():
            old_name = file_path.name
            new_name = normalize_filename(old_name)
            
            # Skip if name is already normalized
            if old_name == new_name:
                continue
                
            try:
                new_path = file_path.parent / new_name
                file_path.rename(new_path)
                logger.info(f"Renamed: {old_name} -> {new_name}")
            except Exception as e:
                logger.error(f"Error renaming {old_name}: {str(e)}")

def fix_imports(file_path: Path):
    """Fix import statements in a Python file."""
    if not file_path.exists() or file_path.suffix != '.py':
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix relative imports
        content = re.sub(
            r'from \.interfaces import',
            'from src.interfaces import',
            content
        )
        
        # Fix direct imports
        content = re.sub(
            r'from interfaces import',
            'from src.interfaces import',
            content
        )
        
        # Write back if changes were made
        if content != f.read():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Fixed imports in: {file_path}")
            
    except Exception as e:
        logger.error(f"Error fixing imports in {file_path}: {str(e)}")

def main():
    """Main function to fix both file names and imports."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Rename files in test documents
    test_docs_dir = project_root / "test_documents"
    if test_docs_dir.exists():
        logger.info("Renaming test documents...")
        for subdir in ["policies", "audits"]:
            dir_path = test_docs_dir / subdir
            if dir_path.exists():
                rename_files(str(dir_path))
    
    # Fix imports in Python files
    logger.info("Fixing imports in Python files...")
    for py_file in project_root.rglob("*.py"):
        fix_imports(py_file)

if __name__ == "__main__":
    main() 