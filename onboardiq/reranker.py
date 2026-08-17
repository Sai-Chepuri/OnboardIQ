import json
import re
from typing import Sequence, Optional, List
from langchain_core.documents import BaseDocumentCompressor, Document
from langchain_core.callbacks import Callbacks
from langchain_core.language_models import BaseChatModel

class LLMReranker(BaseDocumentCompressor):
    """Custom LangChain document compressor implementing the list-wise RankGPT reranking pattern."""
    
    llm: BaseChatModel
    top_n: int = 5

    class Config:
        arbitrary_types_allowed = True

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None
    ) -> Sequence[Document]:
        if not documents:
            return []
            
        # Format documents list for the LLM
        doc_list_str = ""
        for i, doc in enumerate(documents):
            source = doc.metadata.get("source", "Unknown Source")
            # We truncate document content slightly in the prompt to prevent context limit issues, 
            # though we keep the full chunk intact in the actual output.
            content_snippet = doc.page_content[:1500]
            doc_list_str += f"--- Document [{i}] (Source: {source}) ---\n{content_snippet}\n\n"

        system_instruction = (
            "You are a precise search results reranker. Your task is to rank a list of documents "
            "based on their relevance to a user query. You must return a JSON list of document indices "
            "sorted by relevance, from most relevant to least relevant. "
            "Example output: [2, 0, 1, 3]"
        )

        user_prompt = f"""Query: {query}

Documents to rank:
{doc_list_str}
Sort the indices [0 to {len(documents)-1}] by relevance to the query. Return ONLY a valid JSON list of integers (e.g. [2, 0, 1]). Do not explain your reasoning."""

        try:
            # Call the LLM
            response = self.llm.invoke([
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ])
            
            content = response.content
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        text_parts.append(part["text"])
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = "".join(text_parts)
                
            content = content.strip()
            # Remove markdown code block wrappers if any
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\n|```$", "", content, flags=re.MULTILINE).strip()
            
            ranked_indices = json.loads(content)
            
            if not isinstance(ranked_indices, list):
                raise ValueError("Output is not a list")
                
            # Filter and validate indices
            seen = set()
            valid_indices = []
            for idx in ranked_indices:
                try:
                    idx_int = int(idx)
                    if 0 <= idx_int < len(documents) and idx_int not in seen:
                        valid_indices.append(idx_int)
                        seen.add(idx_int)
                except (ValueError, TypeError):
                    continue
            
            # Append any missing indices in original order for safety
            for i in range(len(documents)):
                if i not in seen:
                    valid_indices.append(i)
                    
            print(f"[Reranker] Sorted indices: original={list(range(len(documents)))} -> ranked={valid_indices}")
            
            # Reorder documents and return top N
            reranked_docs = [documents[idx] for idx in valid_indices]
            return reranked_docs[:self.top_n]
            
        except Exception as e:
            print(f"[Reranker] Error during LLM reranking: {e}. Falling back to original order.")
            return list(documents)[:self.top_n]
