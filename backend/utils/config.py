"""Central configuration for the FinMate application."""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "finmate")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

TEMPERATURE = 0.3
MAX_TOKENS = 2048
TOP_P = 0.9

CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge_base")
TRANSACTIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample_transactions")

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
if LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY
