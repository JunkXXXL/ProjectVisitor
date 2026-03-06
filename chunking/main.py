import pymupdf
import tiktoken
import uuid
from utils import *
from dotenv import load_dotenv

load_dotenv()


from elasticsearch import Elasticsearch
ES = Elasticsearch("http://localhost:9221", basic_auth=["user", "infini_rag_flow"], verify_certs=False)

create_index(ES, "new_chunking", 1024)

pdf_paths = collect_pdf_paths(r"D:\chunking\Chemical Technology\article")
for pdf in pdf_paths:
    doc = pymupdf.open(pdf)  # open a document
    pages = []
    for page in doc:  # iterate the document pages
        page = page.get_text()  # get plain text encoded as UTF-8
        pages.append(page)
    index_chunks(ES, "new_chunking", uuid.uuid4().hex, pages)
