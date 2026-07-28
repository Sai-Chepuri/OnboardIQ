import sys
from pathlib import Path
from typing import Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

# Import project files
from onboardiq.config import DATA_DIR
from onboardiq.markdown_loader import MarkdownFrontmatterLoader
from onboardiq.confluence_loader import ConfluenceHTMLLoader
from onboardiq.slack_loader import SlackDirectoryLoader
from onboardiq.chunker import WorkspaceChunker
from onboardiq.vector_store import get_vector_store
from onboardiq.retriever import build_bm25_index, get_hybrid_retriever, get_reranked_retriever, RBACRetriever
from onboardiq.test_indexer import MockEmbeddings
class MockRerankerLLM(BaseChatModel):
    """Mock LLM to test RankGPT list-wise reranking without executing live API calls."""
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> ChatResult:
        import re
        user_message = messages[-1].content
        
        # Find document counts from prompt like "Sort the indices [0 to 9]"
        match = re.search(r"\[0 to (\d+)\]", user_message)
        if match:
            max_idx = int(match.group(1))
            indices = list(range(max_idx + 1))
            # Reverse the list of indices to simulate a custom reranking decision
            indices.reverse()
            content = f"```json\n{indices}\n```"
        else:
            content = "[]"
            
        generation = ChatGeneration(message=AIMessage(content=content))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mock-reranker"

def load_all_documents_rbac():
    """Loads all dummy files using RBAC-aware loaders."""
    docs = []
    
    # 1. Load standard markdown
    markdown_path = DATA_DIR / "markdown" / "payment_gateway.md"
    if markdown_path.exists():
        loader = MarkdownFrontmatterLoader(markdown_path)
        docs.extend(loader.load())

    # 2. Load Notion markdown
    for notion_path in (DATA_DIR / "notion").glob("*.md"):
        loader = MarkdownFrontmatterLoader(notion_path)
        docs.extend(loader.load())

    # 3. Load Confluence HTML
    confluence_path = DATA_DIR / "confluence" / "release_runbook.html"
    if confluence_path.exists():
        loader = ConfluenceHTMLLoader(confluence_path)
        docs.extend(loader.load())

    # 4. Load Slack JSON
    slack_loader = SlackDirectoryLoader(DATA_DIR / "slack")
    docs.extend(slack_loader.load())

    return docs

def test_rbac_retrieval():
    print("=== Testing Permission-Aware RBAC Retrieval Pipeline ===")
    
    # 1. Load and chunk documents
    docs = load_all_documents_rbac()
    chunker = WorkspaceChunker(chunk_size=400, chunk_overlap=50)
    chunks = chunker.split_documents(docs)
    print(f"Loaded {len(chunks)} chunks with access roles mapped.")

    # Print a summary of roles in chunks
    print("\n--- Summary of chunks by Access Roles ---")
    for chunk in chunks:
        source_name = Path(chunk.metadata.get("source", "")).name
        roles = chunk.metadata.get("access_roles")
        print(f"Source: {source_name} | Roles allowed: {roles}")

    # 2. Rebuild index databases
    print("\nBuilding sparse and dense indexes...")
    build_bm25_index(chunks)
    vector_store = get_vector_store(MockEmbeddings())
    # Add documents to local vector store
    vector_store.add_documents(chunks)

    # 3. Setup Hybrid base retriever
    hybrid_retriever = get_hybrid_retriever(
        vector_store=vector_store,
        dense_k=10,
        sparse_k=10
    )

    query = "database migrations postgresql deployment release"

    # --- Case A: Developer Role ---
    print("\n[Query Scenario A] User Role: 'engineering'")
    rbac_retriever_eng = RBACRetriever(base_retriever=hybrid_retriever, user_role="engineering")
    reranked_retriever_eng = get_reranked_retriever(base_retriever=rbac_retriever_eng, reranker_llm=MockRerankerLLM(), top_n=5)
    
    results_eng = reranked_retriever_eng.invoke(query)
    print(f"Returned {len(results_eng)} chunks for 'engineering'.")
    for doc in results_eng:
        source_name = Path(doc.metadata.get("source")).name
        print(f"  - Allowed Chunks: {source_name} (Roles: {doc.metadata.get('access_roles')})")
        assert "release_runbook.html" not in source_name, "Security Breach: Engineering role accessed Ops runbook!"

    # --- Case B: Operations Role ---
    print("\n[Query Scenario B] User Role: 'ops'")
    rbac_retriever_ops = RBACRetriever(base_retriever=hybrid_retriever, user_role="ops")
    reranked_retriever_ops = get_reranked_retriever(base_retriever=rbac_retriever_ops, reranker_llm=MockRerankerLLM(), top_n=5)
    
    results_ops = reranked_retriever_ops.invoke(query)
    print(f"Returned {len(results_ops)} chunks for 'ops'.")
    for doc in results_ops:
        source_name = Path(doc.metadata.get("source")).name
        print(f"  - Allowed Chunks: {source_name} (Roles: {doc.metadata.get('access_roles')})")
        assert "adr_postgresql.md" not in source_name, "Security Breach: Ops role accessed Engineering ADR!"
        assert "engineering_onboarding.md" not in source_name, "Security Breach: Ops role accessed Eng checklist!"

    # --- Case C: Admin Role ---
    print("\n[Query Scenario C] User Role: 'admin'")
    rbac_retriever_admin = RBACRetriever(base_retriever=hybrid_retriever, user_role="admin")
    reranked_retriever_admin = get_reranked_retriever(base_retriever=rbac_retriever_admin, reranker_llm=MockRerankerLLM(), top_n=5)
    
    results_admin = reranked_retriever_admin.invoke(query)
    print(f"Returned {len(results_admin)} chunks for 'admin'.")
    sources = [Path(doc.metadata.get("source")).name for doc in results_admin]
    print(f"Admin saw chunks from: {list(set(sources))}")
    assert len(results_admin) > 0

    print("\n=== RBAC Internal Isolation Verified Successfully! ===")

if __name__ == "__main__":
    test_rbac_retrieval()
