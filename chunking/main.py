import pymupdf
from utils import *
from dotenv import load_dotenv
from clearml import Task

load_dotenv()
task = Task.init(project_name='Chunking', task_name='process_dataset_VladPC')
logger = task.get_logger()


from elasticsearch import Elasticsearch
ES = Elasticsearch("http://localhost:9221", basic_auth=["user", "infini_rag_flow"], verify_certs=False)

create_index_chunks(ES, "chunking_index", 1024)
create_index_books(ES, "book_index", 1024)

pdf_paths = collect_pdf_paths(r"D:\chunking\Chemical Technology\article")
for index, pdf in enumerate(pdf_paths):
    logger.report_scalar(
        title="Progress",
        series="Processed Files",
        value=index + 1,
        iteration=index
    )

    doc = pymupdf.open(pdf)  # open a document
    pages = []
    for page in doc:  # iterate the document pages
        page = clean_article_text(page.get_text())  # get plain text encoded as UTF-8
        pages.append(page)
    insert_file_record(ES, "book_index", pages[0], pdf.name)
    insert_chunk_records_bulk(ES, "chunking_index", pages, pdf.name)
