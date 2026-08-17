import os
from pathlib import Path
from typing import Any, List, Optional
from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "db"

# Create directories if they do not exist
DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "markdown").mkdir(exist_ok=True)
(DATA_DIR / "notion").mkdir(exist_ok=True)
(DATA_DIR / "confluence").mkdir(exist_ok=True)
(DATA_DIR / "slack").mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# Configuration settings
VECTOR_STORE_PATH = DB_DIR / "vector_store.json"
RECORD_MANAGER_DB_PATH = DB_DIR / "record_manager.db"
BM25_INDEX_PATH = DB_DIR / "bm25_index.pkl"

# Chunking configurations
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Model configurations
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

DEFAULT_PROVIDER = (
    "gemini" if GEMINI_API_KEY 
    else ("openai" if OPENAI_API_KEY 
          else ("anthropic" if ANTHROPIC_API_KEY else "mock"))
)

# Embedding models
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"

# Generation & Reranking LLMs
OPENAI_CHAT_MODEL = "gpt-4o"
OPENAI_FAST_MODEL = "gpt-4o-mini"

GEMINI_CHAT_MODEL = "gemini-3.6-flash"
GEMINI_FAST_MODEL = "gemini-3.6-flash"

ANTHROPIC_CHAT_MODEL = "claude-3-5-sonnet-20241022"
ANTHROPIC_FAST_MODEL = "claude-3-5-haiku-20241022"

class MockEmbeddings(Embeddings):
    """Local API-free Mock Embeddings for offline testing."""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1] * 128 for _ in texts]
    def embed_query(self, text: str) -> List[float]:
        return [0.1] * 128

class MockChatModel(BaseChatModel):
    """Local API-free Mock LLM for offline testing."""
    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        user_msg = messages[-1].content
        
        # Check if Reranking request
        if "Sort the indices" in user_msg or "sorted by relevance" in user_msg:
            import re
            match = re.search(r"\[0 to (\d+)\]", user_msg)
            if match:
                max_idx = int(match.group(1))
                indices = list(range(max_idx + 1))
                indices.reverse()  # reverse indices to simulate reranking
                content = f"```json\n{indices}\n```"
            else:
                content = "[]"
        else:
            # Answer generation request
            content = (
                "**[Mock Copilot Answer]** To view live generated answers from Gemini or OpenAI, "
                "please configure your `GEMINI_API_KEY` or `OPENAI_API_KEY` inside your `.env` file.\n\n"
                "Here is what was found in the retrieved context:\n"
            )
            
        generation = ChatGeneration(message=AIMessage(content=content))
        return ChatResult(generations=[generation])

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"

def get_embeddings():
    """Initializes and returns the configured LangChain embeddings class. Falls back to MockEmbeddings offline."""
    # Note: Anthropic has no native embeddings API. We will use Gemini or OpenAI embeddings if keys exist,
    # otherwise fallback to MockEmbeddings.
    if GEMINI_API_KEY:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model=GEMINI_EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY)
    elif OPENAI_API_KEY:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)
    else:
        print("[Notice] Running with API-free MockEmbeddings. Set API keys in .env for live embeddings.")
        return MockEmbeddings()

def get_llm(fast=False):
    """Initializes and returns the configured LangChain chat model. Falls back to MockChatModel offline."""
    if DEFAULT_PROVIDER == "gemini" and GEMINI_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_name = GEMINI_FAST_MODEL if fast else GEMINI_CHAT_MODEL
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=GEMINI_API_KEY, temperature=0.0)
    elif DEFAULT_PROVIDER == "openai" and OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        model_name = OPENAI_FAST_MODEL if fast else OPENAI_CHAT_MODEL
        return ChatOpenAI(model=model_name, openai_api_key=OPENAI_API_KEY, temperature=0.0)
    elif DEFAULT_PROVIDER == "anthropic" and ANTHROPIC_API_KEY:
        from langchain_anthropic import ChatAnthropic
        model_name = ANTHROPIC_FAST_MODEL if fast else ANTHROPIC_CHAT_MODEL
        return ChatAnthropic(model=model_name, api_key=ANTHROPIC_API_KEY, temperature=0.0)
    else:
        print("[Notice] Running with API-free MockChatModel. Set API keys in .env for live chat completions.")
        return MockChatModel()
