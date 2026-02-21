from importlib import metadata
from pathlib import Path
from typing import List
import docling
from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVector, PGVectorStore, PGEngine
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from numpy import format_float_positional
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_core.tools import create_retriever_tool
from ollama import EmbedResponse
from pydantic import UUID4

from src.api.db.schema import EmbeddingResponse


source = Path("/home/krishna/projects/otis/experiments/uploads")
headers_to_split = [("#", "heading"), ("##", "section"), ("###", "subsection")]

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.do_table_structure = False

converter = DocumentConverter(
    format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
)

recursive_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=100, add_start_index=True
)

markdown_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split, strip_headers=False
)

embeddings = OllamaEmbeddings(model="nomic-embed-text")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="collection_name",
    connection="postgresql+psycopg://user:password@db:5432/otis",
)


async def create_vector_store(collection_name: str) -> PGVector:

    embeddings = OllamaEmbeddings(
        model="nomic-embed-text", base_url="http://ollama:11434"
    )

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection="postgresql+psycopg://user:password@db:5432/otis",
    )

    return vector_store


retriever = vector_store.as_retriever(
    search_type="mmr", search_kwargs={"k": 5, "fetch_k": 10, "lamdba_mult": 0.5}
)


async def embed_docs(files: List[str], collection_name: str):

    docling_docs: List[EmbeddingResponse] = []

    vector_store = await create_vector_store(collection_name)

    for file in files:
        result = converter.convert(file)
        md = result.document.export_to_markdown()

        header_docs = markdown_splitter.split_text(md)

        for doc in header_docs:

            if len(doc.page_content) > 800:
                split_docs = recursive_splitter.split_text(doc.page_content)
                for sdoc in split_docs:
                    docling_docs.append(
                        Document(
                            page_content=sdoc,
                            metadata={
                                "source": str(file),
                                "file_name": Path(file).name,
                            },
                        )
                    )
            else:
                docling_docs.append(
                    Document(
                        page_content=doc.page_content,
                        metadata={"source": str(file), "file_name": Path(file).name},
                    )
                )

    vector_store.add_documents(documents=docling_docs)

    return files.__len__()


retriever_tool = create_retriever_tool(
    retriever,
    "retrieve_documents",
    "search and retrieve information from the vectorstore containing documents related to FAISS and RAG",
)


if __name__ == "__main__":

    docling_docs: List[Document] = []

    for file in source.rglob("*.pdf"):
        result = converter.convert(file)
        md = result.document.export_to_markdown()

        header_docs = markdown_splitter.split_text(md)

        for doc in header_docs:

            if len(doc.page_content) > 800:
                split_docs = recursive_splitter.split_text(doc.page_content)
                for sdoc in split_docs:
                    docling_docs.append(
                        Document(
                            page_content=sdoc,
                            metadata={"source": str(file), "file_name": file.name},
                        )
                    )
            else:
                docling_docs.append(
                    Document(
                        page_content=doc.page_content,
                        metadata={"source": str(file), "file_name": file.name},
                    )
                )

    for doc in docling_docs:
        print(doc.metadata)

    vector_store.add_documents(documents=docling_docs)

    result = vector_store.similarity_search(
        "What is rag token?",
    )

    for r in result:
        print(r.page_content, r.id)
