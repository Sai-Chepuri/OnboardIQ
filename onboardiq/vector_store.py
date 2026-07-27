from pathlib import Path
from langchain_core.vectorstores import InMemoryVectorStore
from onboardiq.config import VECTOR_STORE_PATH

def get_vector_store(embeddings) -> InMemoryVectorStore:
    """Loads the persistent InMemoryVectorStore from disk, or creates a new one if it doesn't exist."""
    store_path = Path(VECTOR_STORE_PATH)
    
    if store_path.exists():
        try:
            print(f"Loading persistent vector store from {store_path}")
            return InMemoryVectorStore.load(str(store_path), embeddings)
        except Exception as e:
            print(f"Error loading vector store from {store_path}: {e}. Creating a new one.")
    
    print("Initializing a new in-memory vector store...")
    return InMemoryVectorStore(embeddings)

def save_vector_store(store: InMemoryVectorStore):
    """Saves the InMemoryVectorStore state to disk."""
    store_path = Path(VECTOR_STORE_PATH)
    # Ensure parent dir exists
    store_path.parent.mkdir(exist_ok=True, parents=True)
    
    try:
        store.dump(str(store_path))
        print(f"Successfully serialized and saved vector store to {store_path}")
    except Exception as e:
        print(f"Error saving vector store: {e}")
