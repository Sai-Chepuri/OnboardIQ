import sys
import shutil
from pathlib import Path
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore

# Import our project modules
from onboardiq.config import DB_DIR
from onboardiq.test_chunker import load_all_documents
from onboardiq.chunker import WorkspaceChunker
from onboardiq.vector_store import get_vector_store
from onboardiq.indexer import get_record_manager, index_chunks

class MockEmbeddings(Embeddings):
    """Mock embeddings that return constant vectors for fast, API-free testing."""
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 128 for _ in texts]
        
    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 128

def test_incremental_indexing():
    print("=== Testing Incremental Indexing Pipeline ===")
    
    # 1. Clean up old databases to ensure a fresh test run
    if DB_DIR.exists():
        print(f"Cleaning up database directory {DB_DIR} for clean test...")
        shutil.rmtree(DB_DIR)
    DB_DIR.mkdir(exist_ok=True)

    # 2. Load and chunk documents
    print("Loading and chunking mock documents...")
    docs = load_all_documents()
    chunker = WorkspaceChunker(chunk_size=400, chunk_overlap=50)
    chunks = chunker.split_documents(docs)
    print(f"Loaded {len(docs)} documents which split into {len(chunks)} chunks.")

    # 3. Initialize mock embeddings & vector store
    mock_embeddings = MockEmbeddings()
    vector_store = get_vector_store(mock_embeddings)
    record_manager = get_record_manager()

    # --- Run 1: Initial Ingestion ---
    print("\n--- Ingestion Run 1: Initial load ---")
    res1 = index_chunks(chunks, vector_store, record_manager)
    print(f"Result Run 1: {res1}")
    assert res1["num_added"] > 0, "Should have added documents in initial run."
    assert res1["num_skipped"] == 0, "No documents should be skipped on fresh run."

    # --- Run 2: Re-ingest Unchanged Files ---
    print("\n--- Ingestion Run 2: Re-run with no changes ---")
    # Reload store to test deserialization from disk
    vector_store_2 = get_vector_store(mock_embeddings)
    res2 = index_chunks(chunks, vector_store_2, record_manager)
    print(f"Result Run 2: {res2}")
    assert res2["num_added"] == 0, "No new documents should be added."
    assert res2["num_skipped"] == len(chunks), "All documents should be skipped."

    # --- Run 3: Modify a Document ---
    print("\n--- Ingestion Run 3: Modify one file ---")
    modified_chunks = [c.copy() for c in chunks]
    
    # Find chunks belonging to payment_gateway.md and modify them
    modified_count = 0
    for chunk in modified_chunks:
        if "payment_gateway.md" in chunk.metadata.get("source", ""):
            chunk.page_content += "\nUPDATED RULE: Deployments require signoff from Alice Vance."
            modified_count += 1
            
    print(f"Modified {modified_count} chunks from 'payment_gateway.md'. Running indexer...")
    vector_store_3 = get_vector_store(mock_embeddings)
    res3 = index_chunks(modified_chunks, vector_store_3, record_manager)
    print(f"Result Run 3: {res3}")
    
    assert res3["num_added"] == modified_count, f"Should have updated only {modified_count} chunks."
    assert res3["num_deleted"] == modified_count, f"Should have deleted {modified_count} old chunks."
    assert res3["num_skipped"] == (len(chunks) - modified_count), "Rest of the chunks should remain skipped."

    print("\n=== Incremental Indexing Verified Successfully! ===")

if __name__ == "__main__":
    test_incremental_indexing()
