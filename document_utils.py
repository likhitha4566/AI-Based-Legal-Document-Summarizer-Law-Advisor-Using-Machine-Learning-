from docx import Document
from pypdf import PdfReader

def read_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def read_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def read_txt(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()
