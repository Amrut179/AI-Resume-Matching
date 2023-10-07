import os
import io
import docx2txt
from bs4 import BeautifulSoup
import fitz  # PyMuPDF

def extract_text_from_docx(docx_path):
    text = docx2txt.process(io.BytesIO(docx_path))
    return text

def extract_text_from_pdf(pdf_path):
    text = ''
    links = []
    doc = fitz.open(stream=pdf_path, filetype="pdf")

    for page_num in range(doc.page_count):
        page = doc[page_num]
        page_text = page.get_text("text")
        text += " "+page_text

        for link in page.get_links():
            if "uri" in link:
                links.append(link["uri"])

    links.append(text)
    return " ".join(links)

def extract_text_from_html(html_path):
    soup = BeautifulSoup(html_path, 'html.parser')
    text = soup.get_text()
    return text

def get_resume_text(file_name, resume_path):
    resume_text = ''
    if file_name.endswith('.docx'):
        resume_text = extract_text_from_docx(resume_path)
    elif file_name.endswith('.pdf'):
        resume_text = extract_text_from_pdf(resume_path)
    elif file_name.endswith('.html'):
        resume_text = extract_text_from_html(resume_path)
    else:
        os.remove(resume_path)
        raise ValueError("Unsupported resume format")
    return resume_text

def clear_uploads():
    folder_path = "uploads"
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        
        for file_name in files:
            file_path = os.path.join(folder_path, file_name)
            
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {str(e)}")
    else:
        print(f"The folder path '{folder_path}' does not exist.")