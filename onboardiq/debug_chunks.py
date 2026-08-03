import json
from pathlib import Path
from onboardiq.config import DB_DIR, VECTOR_STORE_PATH
from onboardiq.test_indexer import MockEmbeddings
from onboardiq.vector_store import get_vector_store

def debug_indexed_chunks():
    """Reads the persistent vector store from disk and prints a summary of all indexed chunks."""
    store_path = Path(VECTOR_STORE_PATH)
    
    if not store_path.exists():
        print(f"Error: Vector store file not found at {store_path}.")
        print("Please run 'PYTHONPATH=. .venv/bin/python onboardiq/test_retriever.py' first to populate the database.")
        return

    # Load store using our mock embeddings (so it requires no API keys to inspect)
    print(f"Loading vector database from: {store_path}")
    vector_store = get_vector_store(MockEmbeddings())
    
    # Extract documents from InMemoryVectorStore
    # The underlying storage in InMemoryVectorStore is a dictionary: store.store
    # mapping ID -> (vector, doc_dict) or similar depending on LangChain version.
    # Let's inspect the keys and list documents.
    docs = []
    try:
        # In newer LangChain versions, InMemoryVectorStore stores docs in store.store (dict of id -> Document)
        if hasattr(vector_store, "store"):
            docs = list(vector_store.store.values())
        else:
            print("Could not find standard document dictionary in the vector store instance.")
            return
    except Exception as e:
        print(f"Error extracting documents: {e}")
        return

    print(f"\n==================================================")
    print(f"   ONBOARDIQ VECTOR STORE DEBUGGER")
    print(f"   Total Chunks Indexed: {len(docs)}")
    print(f"==================================================\n")

    # Group chunks by source file for a clean report
    by_source = {}
    for doc in docs:
        source = doc.get("metadata", {}).get("source", "Unknown Source")
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(doc)

    for source_file, chunks in by_source.items():
        print(f"📁 Source: {source_file}")
        print(f"   ├─ Access Roles: {chunks[0].get('metadata', {}).get('access_roles', ['all'])}")
        print(f"   ├─ Number of Chunks: {len(chunks)}")
        print(f"   └─ Chunks List:")
        
        for i, chunk in enumerate(chunks):
            # Try to identify header context
            headers = []
            chunk_metadata = chunk.get("metadata", {})
            if "Header 1" in chunk_metadata:
                headers.append(chunk_metadata["Header 1"])
            if "Header 2" in chunk_metadata:
                headers.append(chunk_metadata["Header 2"])
            if "Header 3" in chunk_metadata:
                headers.append(chunk_metadata["Header 3"])
            
            header_path = " > ".join(headers) if headers else "None (Conversational / Flat)"
            
            # Format preview snippet
            content_preview = chunk.get("text", "").replace("\n", " ")
            if len(content_preview) > 80:
                content_preview = content_preview[:77] + "..."

            print(f"      [{i}] Path: {header_path}")
            print(f"          Snippet: \"{content_preview}\"")
        print()

if __name__ == "__main__":
    debug_indexed_chunks()
