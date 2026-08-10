import pickle
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever

from onboardiq.config import BM25_INDEX_PATH
from onboardiq.reranker import LLMReranker

class RBACRetriever(BaseRetriever):
    """LangChain Retriever wrapper that filters document chunks based on user roles (RBAC) and metadata attributes."""
    
    base_retriever: BaseRetriever
    user_role: str = "all"
    metadata_filter: Optional[dict] = None

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        # 1. Retrieve candidates from underlying dense/sparse/hybrid retriever
        docs = self.base_retriever.invoke(query, **kwargs)
        
        # 2. Filter docs: allow if 'all' is in roles, user is 'admin', or user_role is allowed
        filtered_docs = []
        for doc in docs:
            allowed_roles = doc.metadata.get("access_roles", ["all"])
            
            # Standardize role comparison (case-insensitive)
            allowed_roles_lower = [r.lower() for r in allowed_roles]
            user_role_lower = self.user_role.lower()

            if (
                "all" in allowed_roles_lower 
                or user_role_lower == "admin" 
                or user_role_lower in allowed_roles_lower
            ):
                # Apply optional manual metadata key-value checks (e.g. type, channel, source)
                if self.metadata_filter:
                    match = True
                    for filter_key, filter_val in self.metadata_filter.items():
                        # Handle case-insensitive values if they are strings
                        val = doc.metadata.get(filter_key)
                        if isinstance(val, str) and isinstance(filter_val, str):
                            if val.lower() != filter_val.lower():
                                match = False
                                break
                        elif val != filter_val:
                            match = False
                            break
                    if match:
                        filtered_docs.append(doc)
                else:
                    filtered_docs.append(doc)
            else:
                print(f"[RBAC Alert] Filtered out document {doc.metadata.get('source')} for role '{self.user_role}'")
                
        return filtered_docs

def save_bm25_index(retriever: BM25Retriever):
    """Pickles and saves the BM25Retriever index to disk."""
    path = Path(BM25_INDEX_PATH)
    path.parent.mkdir(exist_ok=True, parents=True)
    with open(path, "wb") as f:
        pickle.dump(retriever, f)
    print(f"Successfully serialized and saved BM25 index to {path}")

def load_bm25_index() -> Optional[BM25Retriever]:
    """Loads the pickled BM25Retriever index from disk."""
    path = Path(BM25_INDEX_PATH)
    if path.exists():
        try:
            with open(path, "rb") as f:
                print(f"Loading BM25 index from {path}")
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading BM25 index: {e}")
    return None

def build_bm25_index(chunks: List[Document]) -> BM25Retriever:
    """Builds a new BM25 index from document chunks and saves it."""
    retriever = BM25Retriever.from_documents(chunks)
    save_bm25_index(retriever)
    return retriever

def get_hybrid_retriever(
    vector_store: VectorStore,
    dense_k: int = 5,
    sparse_k: int = 5,
    dense_weight: float = 0.5,
    sparse_weight: float = 0.5
) -> EnsembleRetriever:
    """Combines Dense Semantic Search (Vector Store) and Sparse Lexical Search (BM25) using RRF."""
    dense_retriever = vector_store.as_retriever(search_kwargs={"k": dense_k})
    
    sparse_retriever = load_bm25_index()
    if not sparse_retriever:
        print("[Warning] BM25 index was not found on disk. Initializing empty fallback.")
        sparse_retriever = BM25Retriever.from_documents([Document(page_content="Fallback empty index.")])
        
    sparse_retriever.k = sparse_k

    ensemble_retriever = EnsembleRetriever(
        retrievers=[dense_retriever, sparse_retriever],
        weights=[dense_weight, sparse_weight]
    )
    return ensemble_retriever

def get_reranked_retriever(
    base_retriever: BaseRetriever,
    reranker_llm,
    top_n: int = 5
) -> ContextualCompressionRetriever:
    """Chains the base retriever with our custom LLM-based List-wise Reranker (RankGPT)."""
    compressor = LLMReranker(llm=reranker_llm, top_n=top_n)
    
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )
    return compression_retriever
