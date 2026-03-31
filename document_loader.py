import os
from docx import Document
from PyPDF2 import PdfReader

def read_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def read_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text

def read_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def load_documents(folder, label):
    documents = []

    for file in os.listdir(folder):

        # 🔥 VERY IMPORTANT: Skip Word temp files
        if file.startswith("~$"):
            continue

        path = os.path.join(folder, file)

        try:
            if file.endswith(".docx"):
                content = read_docx(path)
            elif file.endswith(".pdf"):
                content = read_pdf(path)
            elif file.endswith(".txt"):
                content = read_txt(path)
            else:
                continue

            if content.strip():
                documents.append({
                    "text": content,
                    "label": label,
                    "source": file
                })

        except Exception as e:
            print(f"[SKIPPED] {file} → {e}")

    return documents
