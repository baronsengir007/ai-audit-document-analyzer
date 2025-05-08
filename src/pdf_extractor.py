import PyPDF2
import logging

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            try:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text()
            except (PyPDF2.errors.PdfReadError, Exception) as e:
                logging.warning(f"Error reading PDF content from {pdf_path}: {e}")
                # Attempt a more basic extraction method if possible
                file.seek(0)  # Reset file pointer
                try:
                    # Try a more basic extraction to at least get some content
                    raw_data = file.read().decode('utf-8', errors='ignore')
                    # Return first 2000 characters as a fallback
                    text = f"[PDF EXTRACTION PARTIAL] {raw_data[:2000]}"
                except Exception as fallback_error:
                    logging.error(f"Fallback extraction failed: {fallback_error}")
                    # Return placeholder text with error info
                    text = f"[PDF EXTRACTION FAILED] This document could not be processed properly. Error: {str(e)}"
    except FileNotFoundError:
        logging.error(f"PDF file not found: {pdf_path}")
        text = "[PDF FILE NOT FOUND]"
    except Exception as e:
        logging.error(f"Unexpected error opening {pdf_path}: {e}")
        text = f"[PDF PROCESSING ERROR] {str(e)}"
        
    # Ensure we always return some text content
    if not text:
        text = "[EMPTY PDF CONTENT]"
        
    return text
