import PyPDF2
from docx import Document
import openpyxl
from pathlib import Path

# --- Extraction functions ---

def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_word(docx_path):
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_text_from_excel(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    text = []
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        for row in ws.iter_rows(values_only=True):
            row_text = [str(cell) for cell in row if cell is not None]
            text.append(" | ".join(row_text))
    return "\n".join(text)

# --- Test extraction ---
if __name__ == "__main__":
    # Test PDF extraction
    pdf_path = Path("docs/KPN FEB 2025.pdf")
    if pdf_path.exists():
        text_pdf = extract_text_from_pdf(str(pdf_path))
        print("\n--- PDF Document Text ---\n")
        print(text_pdf)
    else:
        print(f"PDF file not found: {pdf_path}")

    # Test Word extraction
    word_path = Path("docs/Request for Information Alpha.docx")
    if word_path.exists():
        text_word = extract_text_from_word(str(word_path))
        print("\n--- Word Document Text ---\n")
        print(text_word)
    else:
        print(f"Word file not found: {word_path}")

    # Test Excel extraction
    excel_path = Path("docs/pm-Project Alpha.xlsx")
    if excel_path.exists():
        text_excel = extract_text_from_excel(str(excel_path))
        print("\n--- Excel Document Text ---\n")
        print(text_excel)
    else:
        print(f"Excel file not found: {excel_path}")



