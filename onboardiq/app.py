import sys
from pathlib import Path

# Add project root to sys.path to resolve onboardiq imports when run via streamlit command directly
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
import streamlit as st

# Import project pipeline files
from onboardiq.config import (
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    DEFAULT_PROVIDER,
    get_embeddings,
    get_llm,
    VECTOR_STORE_PATH
)
from onboardiq.vector_store import get_vector_store
from onboardiq.retriever import get_hybrid_retriever
from onboardiq.generator import answer_query

# Configure Streamlit page layout
st.set_page_config(
    page_title="OnboardIQ - Security-Aware Copilot",
    page_icon="🤖",
    layout="centered"
)

# Helper to read chunk count
def get_chunk_count() -> int:
    store_path = Path(VECTOR_STORE_PATH)
    if not store_path.exists():
        return 0
    try:
        with open(store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return len(data.get("store", {}))
    except Exception:
        return 0

# --- Sidebar Controls ---
st.sidebar.markdown("## 🧠 OnboardIQ Console")

# 1. Role Selection (RBAC isolation check)
st.sidebar.markdown("### 👤 User Permission Persona")
user_role = st.sidebar.selectbox(
    "Active Role Profile",
    options=["engineering", "ops", "admin"],
    index=0,
    help="Changes what documents the retrieval pipeline can access under RBAC."
)

role_summaries = {
    "engineering": "💼 Developer Access: View code ADRs and onboarding logs. Blocked from ops release runbooks.",
    "ops": "🚀 DevOps Access: View infrastructure deploy files and checklists. Blocked from developer coding decisions.",
    "admin": "👑 Superuser Access: Full visibility across all workspace sources."
}
st.sidebar.caption(role_summaries[user_role])

# 2. Database & API indicators
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 System Status")
st.sidebar.text(f"Indexed Database Chunks: {get_chunk_count()}")

if GEMINI_API_KEY or OPENAI_API_KEY:
    st.sidebar.success(f"🟢 Connected: {DEFAULT_PROVIDER.upper()}")
else:
    st.sidebar.warning("⚠️ Offline: API-Free Mock Mode")

# 3. Actions
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.messages = []
    st.rerun()

# --- Main Chat Interface ---
st.title("🤖 OnboardIQ Copilot")
st.markdown("Your grounded, security-aware corporate knowledge assistant.")

# Initialize chat session history state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load hybrid retrievers and LLM models
@st.cache_resource
def load_rag_retriever():
    embeddings = get_embeddings()
    vector_store = get_vector_store(embeddings)
    return get_hybrid_retriever(vector_store=vector_store, dense_k=6, sparse_k=6)

try:
    hybrid_retriever = load_rag_retriever()
    chat_llm = get_llm(fast=False)
    fast_llm = get_llm(fast=True)
except Exception as e:
    st.error(f"Failed to initialize RAG pipeline components: {e}")
    st.stop()

# Display chat history bubbles
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar")):
        st.markdown(message["content"])
        # Re-render citations if present in history
        if "sources" in message and message["sources"]:
            with st.expander("🔍 Sources Referenced"):
                for idx, src in enumerate(message["sources"]):
                    st.markdown(f"**[{idx+1}] {src['name']}** (`{src['type']}`)")
                    st.code(src["content"], language="markdown")

# Process user input prompts
if user_prompt := st.chat_input("Ask OnboardIQ a question..."):
    # 1. Render user message bubble
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)
    
    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt,
        "avatar": "👤"
    })
    
    # 2. Render assistant message bubble
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Searching files and generating grounded answer..."):
            # Run grounded Q&A query pipeline
            answer, retrieved_docs = answer_query(
                query=user_prompt,
                user_role=user_role,
                chat_llm=chat_llm,
                fast_llm=fast_llm,
                hybrid_retriever=hybrid_retriever,
                top_n=3
            )
            
            st.markdown(answer)
            
            # Format and list citations
            sources_list = []
            for doc in retrieved_docs:
                sources_list.append({
                    "name": Path(doc.metadata.get("source", "")).name,
                    "type": doc.metadata.get("type", "unknown").upper(),
                    "content": doc.page_content
                })
            
            # Display citations expander
            if sources_list:
                with st.expander("🔍 Sources Referenced"):
                    for idx, src in enumerate(sources_list):
                        st.markdown(f"**[{idx+1}] {src['name']}** (`{src['type']}`)")
                        st.code(src["content"], language="markdown")
            
            # Save assistant message to session history
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "avatar": "🤖",
                "sources": sources_list
            })
