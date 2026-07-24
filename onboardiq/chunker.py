from typing import List
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from onboardiq.config import CHUNK_SIZE, CHUNK_OVERLAP

class WorkspaceChunker:
    """Splits documents using header-aware Markdown splitting followed by recursive splitting."""

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Headers to split on for Markdown/Notion/Confluence
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=True
        )
        
        # Text splitter for final sub-chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True
        )

    def _split_markdown_document(self, doc: Document) -> List[Document]:
        """Splits a single Markdown/Notion/Confluence document, propagating headers as text prefixes."""
        # 1. Split by markdown headers
        header_split_docs = self.markdown_splitter.split_text(doc.page_content)
        
        processed_docs = []
        for split_doc in header_split_docs:
            # 2. Extract header hierarchy from metadata
            headers = []
            if "Header 1" in split_doc.metadata:
                headers.append(split_doc.metadata["Header 1"])
            if "Header 2" in split_doc.metadata:
                headers.append(split_doc.metadata["Header 2"])
            if "Header 3" in split_doc.metadata:
                headers.append(split_doc.metadata["Header 3"])

            # 3. Construct the prefix showing the document path context
            header_prefix = ""
            if headers:
                header_path = " > ".join(headers)
                header_prefix = f"Context: {header_path}\n\n"
            
            # Prepend context prefix to page content
            new_content = header_prefix + split_doc.page_content
            
            # 4. Propagate original document metadata (source, type, authors, space)
            new_metadata = doc.metadata.copy()
            new_metadata.update(split_doc.metadata)  # add headers
            
            processed_docs.append(Document(page_content=new_content, metadata=new_metadata))

        # 5. Run recursive text splitting to enforce chunk size limits
        return self.text_splitter.split_documents(processed_docs)

    def split_documents(self, docs: List[Document]) -> List[Document]:
        """Splits a list of documents. Handles Markdown/HTML with headers, and Slack with standard recursive splits."""
        final_chunks = []
        
        for doc in docs:
            doc_type = doc.metadata.get("type", "unknown")
            
            if doc_type in ["markdown", "confluence"] or doc.metadata.get("source", "").endswith((".md", ".markdown")):
                # Markdown or Confluence documents (with structure)
                chunks = self._split_markdown_document(doc)
                final_chunks.extend(chunks)
            else:
                # Slack logs or raw text (without header layout)
                chunks = self.text_splitter.split_documents([doc])
                final_chunks.extend(chunks)
                
        return final_chunks
