import argparse
import sys
from pathlib import Path
from typing import List
from langchain_core.documents import Document

from onboardiq.config import DATA_DIR, get_embeddings, get_llm
from onboardiq.markdown_loader import MarkdownFrontmatterLoader
from onboardiq.confluence_loader import ConfluenceHTMLLoader
from onboardiq.slack_loader import SlackDirectoryLoader
from onboardiq.chunker import WorkspaceChunker
from onboardiq.vector_store import get_vector_store
from onboardiq.indexer import get_record_manager, index_chunks
from onboardiq.retriever import build_bm25_index, get_hybrid_retriever
from onboardiq.generator import answer_query
from onboardiq.evaluator import run_pipeline_evaluation

def load_documents_from_workspace() -> List[Document]:
    """Loads all corporate documents from workspace directories using RBAC-aware loaders."""
    docs = []
    
    # 1. Load standard markdown files
    markdown_dir = DATA_DIR / "markdown"
    if markdown_dir.exists():
        for file_path in markdown_dir.glob("**/*.md"):
            print(f"[Ingest] Loading Markdown: {file_path.relative_to(DATA_DIR)}")
            loader = MarkdownFrontmatterLoader(file_path)
            docs.extend(loader.load())

    # 2. Load Notion markdown files
    notion_dir = DATA_DIR / "notion"
    if notion_dir.exists():
        for file_path in notion_dir.glob("**/*.md"):
            print(f"[Ingest] Loading Notion Page: {file_path.relative_to(DATA_DIR)}")
            loader = MarkdownFrontmatterLoader(file_path)
            docs.extend(loader.load())

    # 3. Load Confluence HTML exports
    confluence_dir = DATA_DIR / "confluence"
    if confluence_dir.exists():
        for file_path in confluence_dir.glob("**/*.html"):
            print(f"[Ingest] Loading Confluence Page: {file_path.relative_to(DATA_DIR)}")
            loader = ConfluenceHTMLLoader(file_path)
            docs.extend(loader.load())

    # 4. Load Slack export channels
    slack_dir = DATA_DIR / "slack"
    if slack_dir.exists() and any(slack_dir.glob("*.json")):
        print(f"[Ingest] Loading Slack directory: {slack_dir.relative_to(DATA_DIR)}")
        loader = SlackDirectoryLoader(slack_dir)
        docs.extend(loader.load())

    return docs

def run_ingestion() -> dict:
    """Executes the end-to-end ingestion pipeline, indexing dense and sparse databases."""
    print("\n--- Starting OnboardIQ Document Ingestion Pipeline ---")
    
    # 1. Load documents
    raw_docs = load_documents_from_workspace()
    print(f"Loaded {len(raw_docs)} source document objects.")
    
    # 2. Chunk documents
    print("Chunking documents...")
    chunker = WorkspaceChunker()
    chunks = chunker.split_documents(raw_docs)
    print(f"Generated {len(chunks)} chunks.")

    # 3. Ingest into persistent vector store incrementally
    print("Indexing into vector store...")
    embeddings = get_embeddings()
    vector_store = get_vector_store(embeddings)
    record_manager = get_record_manager()
    
    index_results = index_chunks(chunks, vector_store, record_manager)
    print(f"Vector indexing results: {index_results}")

    # 4. Build and save BM25 index
    print("Building BM25 sparse keyword index...")
    build_bm25_index(chunks)
    
    print("--- Ingestion Pipeline Finished Successfully ---\n")
    return index_results

def run_query(query: str, role: str):
    """Initializes the retriever and prints the grounded, secure answer for the query."""
    print(f"\n--- Querying OnboardIQ (User Role: {role}) ---")
    
    embeddings = get_embeddings()
    vector_store = get_vector_store(embeddings)
    
    # Setup hybrid base searcher
    hybrid_retriever = get_hybrid_retriever(
        vector_store=vector_store,
        dense_k=5,
        sparse_k=5
    )
    
    chat_llm = get_llm(fast=False)
    fast_llm = get_llm(fast=True)
    
    # Execute query
    answer, docs = answer_query(
        query=query,
        user_role=role,
        chat_llm=chat_llm,
        fast_llm=fast_llm,
        hybrid_retriever=hybrid_retriever,
        top_n=3
    )
    
    print("\n================== ANSWER ==================")
    print(answer)
    print("============================================\n")
    
    print("Sources referenced:")
    for i, doc in enumerate(docs):
        src = doc.metadata.get("source", "Unknown")
        print(f"  [{i+1}] {Path(src).name} ({doc.metadata.get('type')})")
    print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OnboardIQ Copilot CLI Command Center")
    parser.add_argument("--ingest", action="store_true", help="Run the document ingestion pipeline")
    parser.add_argument("--query", type=str, help="Ask the copilot an onboarding or architecture question")
    parser.add_argument("--role", type=str, default="engineering", choices=["engineering", "ops", "admin"], help="User role for permission check")
    parser.add_argument("--evaluate", action="store_true", help="Run the RAGAS-equivalent automated evaluation suite")
    
    args = parser.parse_args()
    
    if args.ingest:
        run_ingestion()
    elif args.query:
        run_query(args.query, args.role)
    elif args.evaluate:
        run_pipeline_evaluation()
    else:
        # Default behavior: show help
        parser.print_help()
