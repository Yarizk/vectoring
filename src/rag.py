"""
Core RAG (Retrieval-Augmented Generation) logic.
Supports both Ollama (local) and Jatevo API providers.
"""

import requests
import json
from typing import List, Dict, Any, Optional, Literal
from embedder import search as base_search
from search_utils import hybrid_search, search_with_expansion, extract_tickers, get_ticker_summary
from config import (
    LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL,
    JATEVO_BASE_URL, JATEVO_API_KEY, JATEVO_MODEL,
    validate_config
)


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def check_jatevo() -> bool:
    """Check if Jatevo API is accessible."""
    if not JATEVO_API_KEY:
        return False
    try:
        # Simple check - just verify we can connect
        response = requests.get(
            f"{JATEVO_BASE_URL}/models",
            headers={"Authorization": f"Bearer {JATEVO_API_KEY}"},
            timeout=10
        )
        # Jatevo might not have a /models endpoint, so we accept various responses
        return response.status_code in [200, 401, 403, 404]
    except:
        # If connection fails, API might still work (different endpoint structure)
        return True  # Assume ok if we have API key


def list_available_models() -> List[str]:
    """List available models based on provider."""
    if LLM_PROVIDER == "ollama":
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m['name'] for m in data.get('models', [])]
        except:
            pass
        return []
    
    elif LLM_PROVIDER == "jatevo":
        # Jatevo models are defined in config
        return [JATEVO_MODEL]
    
    return []


def generate_prompt(query: str, contexts: List[Dict[str, Any]]) -> str:
    """
    Generate a prompt for the LLM with retrieved context.
    """
    # Build context section
    context_texts = []
    for i, ctx in enumerate(contexts, 1):
        source = ctx['metadata'].get('source', 'unknown')
        
        # Format source info
        if source == 'ksei_json':
            ticker = ctx['metadata'].get('ticker', 'N/A')
            date = ctx['metadata'].get('date', 'N/A')
            chunk_type = ctx['metadata'].get('chunk_type', 'unknown')
            source_info = f"[Source: KSEI JSON - Ticker: {ticker}, Date: {date}, Type: {chunk_type}]"
        elif source == 'ksei_pdf':
            filename = ctx['metadata'].get('filename', 'N/A')
            page = ctx['metadata'].get('page_number', 'N/A')
            source_info = f"[Source: KSEI PDF - File: {filename}, Page: {page}]"
        else:
            source_info = f"[Source: {source}]"
        
        context_texts.append(f"Context {i} {source_info}:\n{ctx['text']}\n")
    
    context_block = "\n".join(context_texts)
    
    # Build the full prompt
    prompt = f"""You are a helpful assistant specializing in Indonesian stock market ownership data from KSEI (Indonesia Central Securities Depository). Answer the user's question based on the provided context information.

IMPORTANT INSTRUCTIONS:
1. Answer based ONLY on the provided context data
2. If the context doesn't contain the answer, say "Maaf, saya tidak menemukan informasi tersebut dalam data yang tersedia."
3. Include specific numbers, percentages, and names when available
4. Cite your sources using the format [Source: ...]
5. Answer in the same language as the question (Indonesian or English)

---
CONTEXT INFORMATION:
{context_block}
---

USER QUESTION: {query}

Provide a clear, accurate answer based on the context above."""

    return prompt


def ask_ollama(
    prompt: str,
    model: str = OLLAMA_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 1024
) -> Dict[str, Any]:
    """Send a prompt to Ollama and get the response."""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "text": data.get('response', '').strip(),
                "error": None
            }
        else:
            return {
                "success": False,
                "text": None,
                "error": f"Ollama returned status {response.status_code}: {response.text}"
            }
    
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "text": None,
            "error": f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. Is Ollama running?"
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "text": None,
            "error": "Request to Ollama timed out."
        }
    except Exception as e:
        return {
            "success": False,
            "text": None,
            "error": f"Error calling Ollama: {str(e)}"
        }


def ask_jatevo(
    prompt: str,
    model: str = JATEVO_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 4096
) -> Dict[str, Any]:
    """
    Send a prompt to Jatevo API and get the response.
    Uses OpenAI-compatible completions API.
    """
    if not JATEVO_API_KEY:
        return {
            "success": False,
            "text": None,
            "error": "JATEVO_API_KEY not configured. Set it in .env file."
        }
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JATEVO_API_KEY}"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        response = requests.post(
            f"{JATEVO_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            # OpenAI-compatible response format
            choices = data.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                content = message.get('content', '').strip()
                return {
                    "success": True,
                    "text": content,
                    "error": None,
                    "usage": data.get('usage', {})
                }
            else:
                return {
                    "success": False,
                    "text": None,
                    "error": "No response content from Jatevo API"
                }
        elif response.status_code == 401:
            return {
                "success": False,
                "text": None,
                "error": "Authentication failed. Check your JATEVO_API_KEY."
            }
        else:
            return {
                "success": False,
                "text": None,
                "error": f"Jatevo API returned status {response.status_code}: {response.text}"
            }
    
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "text": None,
            "error": f"Cannot connect to Jatevo API at {JATEVO_BASE_URL}"
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "text": None,
            "error": "Request to Jatevo API timed out."
        }
    except Exception as e:
        return {
            "success": False,
            "text": None,
            "error": f"Error calling Jatevo API: {str(e)}"
        }


def ask_llm(
    prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4096
) -> Dict[str, Any]:
    """
    Send prompt to configured LLM provider.
    Automatically routes to Ollama or Jatevo based on config.
    """
    if LLM_PROVIDER == "jatevo":
        return ask_jatevo(prompt, temperature=temperature, max_tokens=max_tokens)
    else:
        # Default to Ollama
        return ask_ollama(prompt, temperature=temperature, max_tokens=max_tokens)


def ask(
    question: str,
    n_results: int = 5,
    temperature: float = 0.3,
    use_hybrid_search: bool = True
) -> Dict[str, Any]:
    """
    Complete RAG pipeline: retrieve context and generate answer.
    
    Args:
        question: User question
        n_results: Number of context chunks to retrieve
        temperature: Generation temperature
        use_hybrid_search: Use hybrid search with ticker extraction
    """
    # Validate config
    errors = validate_config()
    if errors:
        return {
            "question": question,
            "answer": None,
            "sources": [],
            "success": False,
            "error": "; ".join(errors)
        }
    
    # Check provider availability
    if LLM_PROVIDER == "ollama" and not check_ollama():
        return {
            "question": question,
            "answer": None,
            "sources": [],
            "success": False,
            "error": f"Ollama is not running at {OLLAMA_BASE_URL}. Please start Ollama first."
        }
    
    # Step 1: Retrieve relevant contexts using hybrid search
    if use_hybrid_search:
        # Try hybrid search first (with ticker extraction)
        contexts = hybrid_search(question, n_results=n_results)
        
        # If no results and tickers detected, try direct ticker summary
        if not contexts:
            tickers = extract_tickers(question)
            for ticker in tickers:
                summary = get_ticker_summary(ticker)
                if summary:
                    contexts = [{
                        'id': f'summary_{ticker}',
                        'text': summary,
                        'metadata': {'ticker': ticker, 'source': 'ksei_json', 'chunk_type': 'ticker_summary'},
                        'distance': 0.0
                    }]
                    break
    else:
        contexts = base_search(question, n_results=n_results)
    
    if not contexts:
        return {
            "question": question,
            "answer": "Maaf, tidak ada data yang relevan ditemukan untuk pertanyaan ini.",
            "sources": [],
            "success": True,
            "error": None
        }
    
    # Step 2: Generate prompt with context
    prompt = generate_prompt(question, contexts)
    
    # Step 3: Get answer from LLM
    llm_response = ask_llm(prompt, temperature=temperature)
    
    if not llm_response['success']:
        return {
            "question": question,
            "answer": None,
            "sources": contexts,
            "success": False,
            "error": llm_response['error']
        }
    
    # Format sources for response
    formatted_sources = []
    for ctx in contexts:
        meta = ctx['metadata']
        source = meta.get('source', 'unknown')
        
        source_info = {
            'source': source,
            'text_preview': ctx['text'][:200] + '...',
            'distance': ctx['distance']
        }
        
        if source == 'ksei_json':
            source_info.update({
                'ticker': meta.get('ticker'),
                'date': meta.get('date'),
                'chunk_type': meta.get('chunk_type')
            })
        elif source == 'ksei_pdf':
            source_info.update({
                'filename': meta.get('filename'),
                'page_number': meta.get('page_number'),
                'month_year': meta.get('month_year')
            })
        
        formatted_sources.append(source_info)
    
    return {
        "question": question,
        "answer": llm_response['text'],
        "sources": formatted_sources,
        "success": True,
        "error": None
    }


def ask_with_metadata_filter(
    question: str,
    ticker: Optional[str] = None,
    date: Optional[str] = None,
    n_results: int = 5
) -> Dict[str, Any]:
    """Ask with optional metadata filtering."""
    # Build filter
    where_filter = {}
    if ticker:
        where_filter['ticker'] = ticker.upper()
    if date:
        where_filter['date'] = date
    
    # Retrieve with filter
    if where_filter:
        contexts = search(question, n_results=n_results, where=where_filter)
    else:
        contexts = search(question, n_results=n_results)
    
    if not contexts:
        return {
            "question": question,
            "answer": f"Maaf, tidak ada data untuk {ticker or 'pertanyaan ini'}.",
            "sources": [],
            "success": True,
            "error": None
        }
    
    # Generate prompt and ask
    prompt = generate_prompt(question, contexts)
    llm_response = ask_llm(prompt)
    
    return {
        "question": question,
        "answer": llm_response['text'] if llm_response['success'] else None,
        "sources": contexts,
        "success": llm_response['success'],
        "error": llm_response['error']
    }


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*50)
    print("KSEI RAG - Interactive Test")
    print(f"Provider: {LLM_PROVIDER}")
    print("="*50)
    
    # Validate config
    errors = validate_config()
    if errors:
        print("\nConfiguration Errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    
    # Check provider status
    if LLM_PROVIDER == "ollama":
        if check_ollama():
            print(f"  Ollama is running at {OLLAMA_BASE_URL}")
            models = list_available_models()
            print(f"  Available models: {models}")
        else:
            print(f"  ERROR: Ollama is not running at {OLLAMA_BASE_URL}")
            sys.exit(1)
    
    elif LLM_PROVIDER == "jatevo":
        print(f"  Jatevo API: {JATEVO_BASE_URL}")
        print(f"  Model: {JATEVO_MODEL}")
        if JATEVO_API_KEY:
            masked_key = JATEVO_API_KEY[:8] + "..." + JATEVO_API_KEY[-4:]
            print(f"  API Key: {masked_key}")
        else:
            print("  ERROR: JATEVO_API_KEY not set")
            sys.exit(1)
    
    print("\nType your question or 'quit' to exit\n")
    
    while True:
        question = input("Question: ").strip()
        
        if question.lower() in ('quit', 'exit', 'q'):
            break
        
        if not question:
            continue
        
        print("\nRetrieving context and generating answer...")
        result = ask(question)
        
        if result['success']:
            print(f"\nAnswer: {result['answer']}")
            print(f"\nSources ({len(result['sources'])}):")
            for i, src in enumerate(result['sources'], 1):
                ticker = src.get('ticker', 'N/A')
                source = src.get('source', 'unknown')
                print(f"  {i}. {source} - {ticker}")
        else:
            print(f"\nError: {result['error']}")
        
        print("\n" + "-"*50)
