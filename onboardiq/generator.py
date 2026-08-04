from typing import List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel

from onboardiq.retriever import RBACRetriever, get_reranked_retriever

# Grounding prompt system message
SYSTEM_PROMPT = """You are OnboardIQ, an intelligent, security-aware corporate onboarding and workspace copilot.
Your goal is to answer the user's question accurately using ONLY the provided document context below.

Strict Grounding Guidelines:
1. Answer the question based ONLY on the retrieved documents listed in the context.
2. If the context does not contain the answer or does not provide enough details, say: "I am sorry, but I do not have access to that information in my current knowledge base." Do NOT attempt to make up or hallucinate any answer.
3. Cite your sources directly in your response. At the bottom of your response, provide a clean markdown list of the files or channels you referenced (e.g. "Sources referenced: [Notion / Engineering Onboarding Checklist], [Slack / #deployment-ops]").
4. Maintain role isolation: you must never reference or use documents that are not explicitly provided in the context below.

Retrieved Context:
{context}"""

def format_docs(docs: List[Document]) -> str:
    """Formats document objects into a structured string context for the LLM prompt."""
    if not docs:
        return "No relevant context found."
        
    formatted = []
    for i, doc in enumerate(docs):
        # Extract clear display source
        source_path = doc.metadata.get("source", "Unknown Source")
        # Simplify path presentation for the LLM
        source_display = Path(source_path).name if "/" in source_path or "\\" in source_path else source_path
        
        doc_type = doc.metadata.get("type", "Document").title()
        title = doc.metadata.get("title", doc.metadata.get("channel", "Workspace File"))
        
        formatted.append(
            f"--- Document [{i}] (Type: {doc_type}, Source: {source_display}, Title: {title}) ---\n"
            f"{doc.page_content}"
        )
    return "\n\n".join(formatted)

def answer_query(
    query: str,
    user_role: str,
    chat_llm: BaseChatModel,
    fast_llm: BaseChatModel,
    hybrid_retriever,
    top_n: int = 3
) -> Tuple[str, List[Document]]:
    """Enforces RBAC role checks, retrieves hybrid search matches, reranks them, and generates a cited response.
    
    Returns:
        Tuple[str, List[Document]]: (Grounded LLM Answer, List of retrieved source Documents used)
    """
    # 1. Wrap hybrid retriever in role-based access control (RBAC) filter
    rbac_retriever = RBACRetriever(
        base_retriever=hybrid_retriever,
        user_role=user_role
    )
    
    # 2. Chain the RBAC retriever with the list-wise LLM reranker
    # Reranking is done on the secure subset of documents
    reranked_retriever = get_reranked_retriever(
        base_retriever=rbac_retriever,
        reranker_llm=fast_llm,
        top_n=top_n
    )
    
    # 3. Retrieve and rerank docs
    print(f"[QA Chain] User '{user_role}' querying: '{query}'")
    retrieved_docs = reranked_retriever.invoke(query)
    
    # 4. Format prompt templates
    context_str = format_docs(retrieved_docs)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{question}")
    ])
    
    # 5. Build LCEL chain and execute
    qa_chain = prompt | chat_llm | StrOutputParser()
    
    answer = qa_chain.invoke({
        "context": context_str,
        "question": query
    })
    
    return answer, retrieved_docs
# To handle simple path extraction in format_docs
from pathlib import Path
