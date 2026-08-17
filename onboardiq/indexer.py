from typing import List, Dict
from langchain_classic.indexes import SQLRecordManager, index
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from onboardiq.config import RECORD_MANAGER_DB_PATH
from onboardiq.vector_store import save_vector_store

def get_record_manager() -> SQLRecordManager:
    """Initializes and returns the LangChain SQLRecordManager with the SQLite database schema created."""
    db_path = RECORD_MANAGER_DB_PATH
    db_path.parent.mkdir(exist_ok=True, parents=True)
    
    db_url = f"sqlite:///{db_path}"
    namespace = "onboardiq/vectorstore"
    
    record_manager = SQLRecordManager(
        namespace=namespace,
        db_url=db_url
    )
    # Ensure the indexing schema tables exist
    record_manager.create_schema()
    return record_manager

def index_chunks(chunks: List[Document], vector_store: VectorStore, record_manager: SQLRecordManager) -> Dict[str, int]:
    """Runs LangChain's incremental index function over the provided chunks.
    
    Uses cleanup="incremental" to delete chunks of modified files.
    Saves the updated vector store state to disk upon completion.
    """
    if not chunks:
        print("No chunks provided for indexing.")
        return {"num_added": 0, "num_updated": 0, "num_skipped": 0, "num_deleted": 0}

    print(f"Running LangChain indexing API on {len(chunks)} chunks in throttled batches to avoid API rate limits...")
    import time
    batch_size = 50
    final_result = {"num_added": 0, "num_updated": 0, "num_skipped": 0, "num_deleted": 0}
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        print(f"[Throttled Indexer] Indexing batch {i//batch_size + 1}/{-(-len(chunks)//batch_size)} ({len(batch)} chunks)...")
        
        result = index(
            docs_source=batch,
            record_manager=record_manager,
            vector_store=vector_store,
            cleanup="incremental",
            source_id_key="source"
        )
        
        for k in final_result:
            if k in result:
                final_result[k] += result[k]
                
        if i + batch_size < len(chunks):
            print("[Throttled Indexer] Rate-limiting check: sleeping for 30 seconds...")
            time.sleep(30)
            
    print(f"Indexing completed: {final_result}")
    
    # Persist the vector store to disk
    save_vector_store(vector_store)
    
    return final_result
