import os
import PyPDF2
import docx

def extract_text_from_resume(file_field):
    if not file_field: 
        return ""

    try:
        file_path = file_field.path
    except ValueError:
        return ""


    if not os.path.exists(file_path):
        return ""

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return " ".join(page.extract_text() or "" for page in reader.pages)

    elif ext == ".docx":
        doc = docx.Document(file_path)
        return " ".join([p.text for p in doc.paragraphs])

    return ""
