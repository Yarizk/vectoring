"""
Configuration management for KSEI RAG.
Supports both local Ollama and Jatevo API providers.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "jatevo").lower()

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# Jatevo API Configuration
JATEVO_BASE_URL = os.getenv("JATEVO_BASE_URL", "https://jatevo.id/api/open/v1/inference")
JATEVO_API_KEY = os.getenv("JATEVO_API_KEY", "")
JATEVO_MODEL = os.getenv("JATEVO_MODEL", "qwen3.5-plus")

# Market Data API Configuration (optional, enables live enrichment)
STOCKBIT_TOKEN = os.getenv("MARKET_DATA_TOKEN", os.getenv("STOCKBIT_TOKEN", ""))

# Embedding Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ChromaDB Configuration
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))


def get_llm_config():
    """Get current LLM configuration."""
    return {
        "provider": LLM_PROVIDER,
        "ollama": {
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
        },
        "jatevo": {
            "base_url": JATEVO_BASE_URL,
            "api_key": JATEVO_API_KEY,
            "model": JATEVO_MODEL,
        }
    }


def validate_config():
    """Validate configuration based on provider."""
    errors = []
    
    if LLM_PROVIDER == "jatevo":
        if not JATEVO_API_KEY or JATEVO_API_KEY == "your_api_key_here":
            errors.append("JATEVO_API_KEY is required when using Jatevo provider")
    
    elif LLM_PROVIDER == "ollama":
        # Ollama doesn't require API key
        pass
    else:
        errors.append(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use 'ollama' or 'jatevo'")
    
    return errors
