import sys
from pathlib import Path

# Import project files
from onboardiq.config import get_embeddings, get_llm
from onboardiq.vector_store import get_vector_store
from onboardiq.retriever import get_hybrid_retriever
from onboardiq.generator import answer_query

def run_qa_tests():
    print("=== Testing Grounded Generation & QA Chain ===")
    
    # 1. Load the persistent indexes from disk
    embeddings = get_embeddings()
    vector_store = get_vector_store(embeddings)
    
    hybrid_retriever = get_hybrid_retriever(
        vector_store=vector_store,
        dense_k=4,
        sparse_k=4
    )
    
    # 2. Get the LLM models (real or mock depending on API keys)
    chat_llm = get_llm(fast=False)
    fast_llm = get_llm(fast=True)

    # --- Test Case 1: Ops Deploy Runbook (Inside Context) ---
    print("\n--- Test Case 1: In-Context Query (Ops Role) ---")
    query_1 = "How do I deploy to production and verify migrations?"
    role_1 = "ops"
    
    answer_1, docs_1 = answer_query(
        query=query_1,
        user_role=role_1,
        chat_llm=chat_llm,
        fast_llm=fast_llm,
        hybrid_retriever=hybrid_retriever,
        top_n=3
    )
    
    print("\n[Generated Answer]:")
    print(answer_1)
    print("\n[Source Chunks Allowed & Retained]:")
    for i, doc in enumerate(docs_1):
        print(f"  [{i}] Source: {Path(doc.metadata.get('source')).name} | Allowed Roles: {doc.metadata.get('access_roles')}")

    # --- Test Case 2: Out of Context Refusal ---
    print("\n--- Test Case 2: Out-of-Context Query (Engineering Role) ---")
    query_2 = "What is the corporate office Wi-Fi password?"
    role_2 = "engineering"
    
    answer_2, docs_2 = answer_query(
        query=query_2,
        user_role=role_2,
        chat_llm=chat_llm,
        fast_llm=fast_llm,
        hybrid_retriever=hybrid_retriever,
        top_n=3
    )
    
    print("\n[Generated Answer]:")
    print(answer_2)
    print(f"\n[Source Chunks Retained]: {len(docs_2)} chunks.")

if __name__ == "__main__":
    run_qa_tests()
