import os
import json
from pathlib import Path
from .pdf_extractor import extract_text_from_pdf
from .document_processor import extract_text_from_word, extract_text_from_excel


# Supported file extensions
DOC_TYPES = {
    ".pdf": ("pdf", extract_text_from_pdf),
    ".docx": ("word", extract_text_from_word),
    ".xlsx": ("excel", extract_text_from_excel),
}

def load_and_normalize_documents(folder_path):
    normalized_docs = []

    for file in os.listdir(folder_path):
        file_path = Path(folder_path) / file
        ext = file_path.suffix.lower()

        if ext in DOC_TYPES:
            doc_type, extractor_func = DOC_TYPES[ext]
            try:
                content = extractor_func(str(file_path))
                normalized_docs.append({
                    "filename": file,
                    "type": doc_type,
                    "content": content
                })
                print(f"Loaded: {file} ({doc_type})")
            except Exception as e:
                print(f"Error processing {file}: {e}")

    return normalized_docs

if __name__ == "__main__":
    docs_folder = "docs"
    output_folder = "outputs"
    os.makedirs(output_folder, exist_ok=True)

    normalized_data = load_and_normalize_documents(docs_folder)

    output_file = Path(output_folder) / "normalized_docs.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(normalized_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Normalized data saved to {output_file}")
