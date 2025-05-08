import os
from pathlib import Path
import logging

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

if __name__ == "__main__":
    # Rename files in both policy and audit directories
    base_dir = Path("test_documents")
    
    # Rename policy documents
    policy_dir = base_dir / "policies"
    if policy_dir.exists():
        logger.info("Renaming policy documents...")
        rename_files(str(policy_dir))
    
    # Rename audit documents
    audit_dir = base_dir / "audits"
    if audit_dir.exists():
        logger.info("Renaming audit documents...")
        rename_files(str(audit_dir)) 