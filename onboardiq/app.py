import json
import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Import project pipeline files
from onboardiq.config import (
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    DEFAULT_PROVIDER,
    get_embeddings,
    get_llm,
    VECTOR_STORE_PATH
)
from onboardiq.pipeline import run_ingestion
from onboardiq.vector_store import get_vector_store
from onboardiq.retriever import get_hybrid_retriever, get_reranked_retriever, RBACRetriever
from onboardiq.generator import answer_query, format_docs
from onboardiq.evaluator import run_pipeline_evaluation, EVAL_DATASET

# Configure Streamlit page
st.set_page_config(
    page_title="OnboardIQ - Institutional Knowledge Copilot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject modern, premium styling
st.markdown("""
<style>
    /* Main app layout styling */
    .stApp {
        background-color: #0d0e15;
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #161925;
        border-right: 1px solid #2d3142;
    }
    
    /* Title and headers */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    .main-title {
        background: linear-gradient(90deg, #a78bfa 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Card design */
    .glass-card {
        background-color: #1e1b29;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #3c3852;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    
    .source-tag {
        background-color: #312e45;
        border: 1px solid #585375;
        color: #d8b4fe;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.8rem;
        display: inline-block;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    
    .role-tag {
        background-color: #1e3a8a;
        color: #93c5fd;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.8rem;
        display: inline-block;
        font-weight: bold;
    }
    
    /* Highlighted metrics */
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #a78bfa;
    }
</style>
""", unsafe_allow_html=True)

# Helper to load total chunk count
def get_chunk_count() -> int:
    store_path = Path(VECTOR_STORE_PATH)
    if not store_path.exists():
        return 0
    try:
        with open(store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # In InMemoryVectorStore serialization, documents are stored in a dictionary
            # or array under the 'store' key. Let's return length of store keys.
            return len(data.get("store", {}))
    except Exception:
        return 0

# App Layout Header
st.markdown("<h1 class='main-title'>OnboardIQ</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Production RAG Institutional Knowledge Copilot with RBAC Role Isolation</p>", unsafe_allow_html=True)

# --- Sidebar Controls ---
st.sidebar.markdown("### 🛠️ Configuration & Status")

# API Status indicators
api_configured = GEMINI_API_KEY or OPENAI_API_KEY
if api_configured:
    st.sidebar.success(f"🟢 Active API: {DEFAULT_PROVIDER.upper()}")
else:
    st.sidebar.warning("⚠️ Running in API-Free Mock Mode")

# Ingestion trigger
st.sidebar.markdown("---")
st.sidebar.markdown("### 📁 Data Ingestion")
chunk_count = get_chunk_count()
st.sidebar.info(f"Database Chunks Loaded: {chunk_count}")

if st.sidebar.button("🔄 Re-Ingest Workspace Data"):
    with st.spinner("Executing incremental indexing pipeline..."):
        results = run_ingestion()
        st.sidebar.success(f"Ingested successfully!")
        st.sidebar.write(results)
        st.rerun()

# Role Control (RBAC)
st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 User Persona Selection")
user_role = st.sidebar.selectbox(
    "Active Security Role",
    options=["engineering", "ops", "admin"],
    index=0,
    help="Determines role-based access control. Admin has access to all documents."
)
role_descriptions = {
    "engineering": "Accesses onboarding guidelines and database architecture. Restricted from release runbooks.",
    "ops": "Accesses production deployment procedures and release metrics. Restricted from developer code ADRs.",
    "admin": "Full access to all corporate directories."
}
st.sidebar.caption(f"**Description:** {role_descriptions[user_role]}")

# Manual Metadata Filters
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Manual Search Filters")
filter_by_type = st.sidebar.multiselect(
    "Filter by Document Type",
    options=["markdown", "confluence", "slack"],
    default=[],
    help="Uses metadata properties to restrict results. Leave empty for all."
)

# Tabs
tab_chat, tab_debug, tab_eval = st.tabs(["💬 Workspace Chat", "🔍 Retrieval Debugger", "📊 Automated Evaluation"])

# Initialize retriever
@st.cache_resource
def load_base_searchers():
    embeddings = get_embeddings()
    vector_store = get_vector_store(embeddings)
    hybrid_retriever = get_hybrid_retriever(
        vector_store=vector_store,
        dense_k=8,
        sparse_k=8
    )
    return hybrid_retriever

try:
    base_hybrid_retriever = load_base_searchers()
    chat_llm = get_llm(fast=False)
    fast_llm = get_llm(fast=True)
except Exception as e:
    st.error(f"Failed to initialize embedding and LLM components: {e}")
    st.stop()

# --- Tab 1: Chat interface ---
with tab_chat:
    st.markdown("### Ask OnboardIQ")
    st.write("Submit a question to see the grounded answer, active role filters, and source citations.")
    
    # Suggested Questions based on roles
    suggested_q = ""
    if user_role == "engineering":
        suggested_q = st.selectbox("Quick Suggestion (Engineering)", ["", "What do I run if I get database connection error locally?", "What are the staging and production endpoints for payment gateway?"])
    elif user_role == "ops":
        suggested_q = st.selectbox("Quick Suggestion (Ops)", ["", "How do I deploy to production and verify migrations?"])
    
    query_input = st.text_input(
        "Enter your query:",
        value=suggested_q if suggested_q else "",
        placeholder="e.g. How do I setup my local developer database?"
    )

    if query_input:
        # Build manual metadata filter dict if specified
        m_filter = None
        if filter_by_type:
            m_filter = {"type": filter_by_type[0]} # filter by first selection for simplicity
            
        with st.spinner("Processing hybrid search, role checks, and grounded generation..."):
            # Run answer generation
            answer, retrieved_docs = answer_query(
                query=query_input,
                user_role=user_role,
                chat_llm=chat_llm,
                fast_llm=fast_llm,
                hybrid_retriever=base_hybrid_retriever,
                top_n=3,
                metadata_filter=m_filter
            )
            
            # Display Answer Card
            st.markdown(f"<div class='glass-card'><h3>Answer</h3>\n\n{answer}</div>", unsafe_allow_html=True)
            
            # Display citations list
            st.markdown("#### Citations & Retrieved Context")
            if retrieved_docs:
                for idx, doc in enumerate(retrieved_docs):
                    source_name = Path(doc.metadata.get("source", "")).name
                    doc_type = doc.metadata.get("type", "unknown").upper()
                    allowed_roles = doc.metadata.get("access_roles", [])
                    title = doc.metadata.get("title", doc.metadata.get("channel", "Doc"))
                    
                    with st.expander(f"[{idx+1}] {source_name} - Title: {title}"):
                        st.markdown(f"<span class='source-tag'>Type: {doc_type}</span> <span class='source-tag'>Roles: {allowed_roles}</span>", unsafe_allow_html=True)
                        st.code(doc.page_content, language="markdown")
            else:
                st.warning("No documents passed the security check or matching filters for this query.")

# --- Tab 2: Retrieval Debugger ---
with tab_debug:
    st.markdown("### Step-by-Step Retrieval Inspector")
    st.write("Inspect how sparse keyword searches and dense semantic searches are merged and filtered.")
    
    debug_query = st.text_input("Enter a query to inspect retrieval layers:", placeholder="e.g. database schema", key="debug_query")
    
    if debug_query:
        # 1. Fetch raw Dense Vector candidates
        dense_retriever = base_hybrid_retriever.retrievers[0]
        dense_results = dense_retriever.invoke(debug_query)
        
        # 2. Fetch raw Sparse BM25 candidates
        sparse_retriever = base_hybrid_retriever.retrievers[1]
        sparse_results = sparse_retriever.invoke(debug_query)
        
        # 3. Fetch RRF Fused Candidates
        rrf_results = base_hybrid_retriever.invoke(debug_query)
        
        # 4. Fetch RBAC Filtered + Reranked candidates
        m_filter = {"type": filter_by_type[0]} if filter_by_type else None
        rbac_ret = RBACRetriever(base_retriever=base_hybrid_retriever, user_role=user_role, metadata_filter=m_filter)
        rerank_ret = get_reranked_retriever(base_retriever=rbac_ret, reranker_llm=fast_llm, top_n=4)
        rerank_results = rerank_ret.invoke(debug_query)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 1. Dense Semantic Hits (Chroma)")
            for i, doc in enumerate(dense_results[:3]):
                source_name = Path(doc.metadata.get("source", "")).name
                st.markdown(f"**[{i}] {source_name}**  \n`{doc.page_content[:150]}...`  \n*Access Roles: {doc.metadata.get('access_roles')}*")
                st.markdown("---")
                
        with col2:
            st.markdown("#### 2. Sparse Lexical Hits (BM25)")
            for i, doc in enumerate(sparse_results[:3]):
                source_name = Path(doc.metadata.get("source", "")).name
                st.markdown(f"**[{i}] {source_name}**  \n`{doc.page_content[:150]}...`  \n*Access Roles: {doc.metadata.get('access_roles')}*")
                st.markdown("---")
                
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### 3. Reciprocal Rank Fusion (RRF)")
            for i, doc in enumerate(rrf_results[:4]):
                source_name = Path(doc.metadata.get("source", "")).name
                st.markdown(f"**[{i}] {source_name}**  \n`{doc.page_content[:150]}...`  \n*Access Roles: {doc.metadata.get('access_roles')}*")
                st.markdown("---")
                
        with col4:
            st.markdown("#### 4. RBAC Filtered & Reranked (RankGPT)")
            if rerank_results:
                for i, doc in enumerate(rerank_results):
                    source_name = Path(doc.metadata.get("source", "")).name
                    st.markdown(f"**[{i}] {source_name}** ✅ Passed  \n`{doc.page_content[:150]}...`  \n*Access Roles: {doc.metadata.get('access_roles')}*")
                    st.markdown("---")
            else:
                st.error("All retrieved documents were blocked by the active security role filter!")

# --- Tab 3: Evaluation Dashboard ---
with tab_eval:
    st.markdown("### Automated RAG Evaluation")
    st.write("Run the LLM-as-a-Judge validation suite over OnboardIQ's standard evaluation dataset.")
    
    st.markdown("#### Reference Evaluation Dataset")
    eval_df = pd.DataFrame(EVAL_DATASET)
    st.table(eval_df)
    
    if st.button("🚀 Trigger RAGAS-Equivalent Evaluation Suite"):
        with st.spinner("Running pipeline evaluation and calculating judges scores..."):
            results_df = run_pipeline_evaluation()
            
            # Show Metric widgets
            c1, c2, c3 = st.columns(3)
            avg_faith = results_df["Faithfulness"].mean()
            avg_relevance = results_df["Answer Relevance"].mean()
            avg_recall = results_df["Context Recall"].mean()
            
            with c1:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.metric("Average Faithfulness", f"{avg_faith:.2f}", help="Is the answer grounded in context?")
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.metric("Answer Relevance", f"{avg_relevance:.2f}", help="Does the answer address the question?")
                st.markdown("</div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.metric("Context Recall", f"{avg_recall:.2f}", help="Did the search capture all correct context?")
                st.markdown("</div>", unsafe_allow_html=True)
                
            st.markdown("#### Detailed Scores Sheet")
            st.dataframe(results_df, use_container_width=True)
            st.success("Evaluation completed!")
