import pymupdf as fitz
import re
import bs4
from langchain_community.document_loaders import PyMuPDFLoader
#Extract Text
class PDFTextExtractor:

    def __init__(self, pdf_url: str):
        pdf_url=pdf_url.replace("abs","pdf")
        self.pdf_url = pdf_url
    
    def extract_text(self)->str:
        """extract text from pdf using pymupdf"""
        loader=PyMuPDFLoader(self.pdf_url)
        documents=loader.load()
        full_text=""
        for doc in documents:
            full_text+=doc.page_content+"\n"
        return full_text.strip()  
    def clean_text(self, text: str) -> str:
    # Strip HTML tags if any
       bs4_text = bs4.BeautifulSoup(text, "html.parser").get_text()
   
       # Remove multiple newlines and excessive whitespace
       e_cleaned = re.sub(r'\n+', '\n', bs4_text)
       e_cleaned = re.sub(r'[ \t]+', ' ', e_cleaned)
   
       # Remove arXiv math placeholders like @xmath0, @xmath1, etc.
       e_cleaned = re.sub(r'@xmath\d+', '', e_cleaned)
   
       # Normalize <n> artifacts into proper newlines
       e_cleaned = e_cleaned.replace('<n>', '\n')

       return e_cleaned.strip()
    def final_text(self)->str:
        """get cleaned text from pdf"""
        raw_text=self.extract_text()
        cleaned_text=self.clean_text(raw_text)
        return cleaned_text
    
#LLM for the good representation

