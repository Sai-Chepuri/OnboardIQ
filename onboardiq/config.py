import os
from pathlib import Path
from dotenv import load_dotenv

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
# Defaulting to Gemini, but will fall back to OpenAI depending on key availability
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DEFAULT_PROVIDER = "gemini" if GEMINI_API_KEY else "openai"

# Embedding models
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
GEMINI_EMBEDDING_MODEL = "models/text-embedding-004"

# Generation & Reranking LLMs
OPENAI_CHAT_MODEL = "gpt-4o"
OPENAI_FAST_MODEL = "gpt-4o-mini"

GEMINI_CHAT_MODEL = "gemini-1.5-pro"
GEMINI_FAST_MODEL = "gemini-1.5-flash"

def get_embeddings():
    """Initializes and returns the configured LangChain embeddings class."""
    if DEFAULT_PROVIDER == "gemini" and GEMINI_API_KEY:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(model=GEMINI_EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY)
    elif OPENAI_API_KEY:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=OPENAI_EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)
    else:
        raise ValueError("Neither GEMINI_API_KEY nor OPENAI_API_KEY is configured in the environment.")

def get_llm(fast=False):
    """Initializes and returns the configured LangChain chat model."""
    if DEFAULT_PROVIDER == "gemini" and GEMINI_API_KEY:
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_name = GEMINI_FAST_MODEL if fast else GEMINI_CHAT_MODEL
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=GEMINI_API_KEY, temperature=0.0)
    elif OPENAI_API_KEY:
        from langchain_openai import ChatOpenAI
        model_name = OPENAI_FAST_MODEL if fast else OPENAI_CHAT_MODEL
        return ChatOpenAI(model=model_name, openai_api_key=OPENAI_API_KEY, temperature=0.0)
    else:
        raise ValueError("Neither GEMINI_API_KEY nor OPENAI_API_KEY is configured in the environment.")
