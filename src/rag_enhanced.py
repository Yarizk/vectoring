"""
Enhanced RAG with flexible response modes and anti-hallucination features.

Modes:
- strict: Only use retrieved context, no inference
- balanced: Use context + light inference for connections
- explorative: Use context as foundation + broader reasoning
"""

import requests
from typing import List, Dict, Any, Optional
from embedder import search as base_search
from search_utils import hybrid_search, extract_tickers, get_ticker_summary
from stockbit_enricher import enrich_tickers, format_enrichment_for_prompt
from config import (
    LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL,
    JATEVO_BASE_URL, JATEVO_API_KEY, JATEVO_MODEL,
    validate_config
)


# Response mode definitions
RESPONSE_MODES = {
    "strict": {
        "temperature": 0.1,
        "creativity": 0.0,
        "allow_inference": False,
        "allow_general_knowledge": False,
        "confidence_threshold": "high",
        "description": "Only use retrieved data, no assumptions"
    },
    "balanced": {
        "temperature": 0.3,
        "creativity": 0.3,
        "allow_inference": True,
        "allow_general_knowledge": False,
        "confidence_threshold": "medium",
        "description": "Use data + reasonable connections"
    },
    "explorative": {
        "temperature": 0.5,
        "creativity": 0.6,
        "allow_inference": True,
        "allow_general_knowledge": True,
        "confidence_threshold": "low",
        "description": "Broader analysis with clear uncertainty markers"
    }
}


def generate_context_block(contexts: List[Dict[str, Any]]) -> str:
    """Generate formatted context block."""
    context_texts = []
    for i, ctx in enumerate(contexts, 1):
        source = ctx['metadata'].get('source', 'unknown')
        
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
        
        context_texts.append(f"Context {i} {source_info}:\n{ctx['text']}")
    
    return "\n\n".join(context_texts)


def generate_system_prompt(mode: str = "balanced") -> str:
    """Generate system prompt based on mode."""
    mode_config = RESPONSE_MODES.get(mode, RESPONSE_MODES["balanced"])
    
    base_prompt = """You are KSEI Intelligence, an AI assistant specializing in Indonesian stock market ownership data.

CORE PRINCIPLES:
1. HONESTY: Never make up data. Clearly state when information is missing or uncertain.
2. TRANSPARENCY: Distinguish between facts from data vs. reasonable inferences.
3. CLARITY: Answer in the same language as the question (Indonesian or English).
4. CITATION: Always cite your sources for factual claims.

UNCERTAINTY MARKERS:
- Use [CERTAIN] for facts directly from retrieved data
- Use [INFERRED] for reasonable conclusions from data
- Use [UNCERTAIN] for educated guesses with limited data
- Use [NOT_AVAILABLE] when data doesn't exist in context
"""
    
    if mode == "strict":
        return base_prompt + """
STRICT MODE INSTRUCTIONS:
- ONLY use information explicitly stated in the provided context
- DO NOT make any assumptions or inferences
- DO NOT use general knowledge about stocks or companies
- If the answer isn't in the context, say: "I don't have that information in the retrieved data."
- Cite exact numbers and percentages from the sources
"""
    
    elif mode == "balanced":
        return base_prompt + """
BALANCED MODE INSTRUCTIONS:
- Use retrieved data as the foundation
- You may make LIGHT inferences (e.g., "if A owns X and B owns Y, then...")
- Mark inferences clearly with [INFERRED]
- DO NOT use external knowledge not in the context
- If data is incomplete, say what's missing
"""
    
    else:  # explorative
        return base_prompt + """
EXPLORATIVE MODE INSTRUCTIONS:
- Use retrieved data as a foundation for broader analysis
- You may draw connections between data points
- You may use light general knowledge to contextualize (e.g., "this is unusual because...")
- ALWAYS mark when you're going beyond the data: [BEYOND_DATA]
- Be explicit about confidence levels: High/Medium/Low
- Suggest what additional data would be helpful
- If speculating, say "This is speculation, but..."
"""


def analyze_data_quality(contexts: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
    """Analyze the quality and relevance of retrieved data."""
    if not contexts:
        return {
            "has_data": False,
            "quality_score": 0,
            "coverage": "none",
            "gaps": ["No relevant data retrieved"],
            "recommendations": ["Try a more specific query", "Check if data exists for this ticker/time period"]
        }
    
    # Calculate average relevance (distance is inverse of relevance)
    avg_distance = sum(ctx['distance'] for ctx in contexts) / len(contexts)
    relevance_score = max(0, min(100, (1 - avg_distance) * 100))
    
    # Check for different source types
    has_pdf = any(ctx['metadata'].get('source') == 'ksei_pdf' for ctx in contexts)
    has_json = any(ctx['metadata'].get('source') == 'ksei_json' for ctx in contexts)
    
    # Extract tickers found
    tickers_found = set()
    for ctx in contexts:
        ticker = ctx['metadata'].get('ticker')
        if ticker:
            tickers_found.add(ticker)
    
    # Determine coverage
    query_tickers = set(extract_tickers(query))
    matched_tickers = query_tickers & tickers_found
    
    if matched_tickers == query_tickers:
        coverage = "complete"
    elif matched_tickers:
        coverage = "partial"
    else:
        coverage = "minimal"
    
    # Identify gaps
    gaps = []
    recommendations = []
    
    if relevance_score < 50:
        gaps.append("Low relevance matches")
        recommendations.append("Query may be too broad or ambiguous")
    
    if coverage == "partial":
        missing = query_tickers - tickers_found
        gaps.append(f"Missing data for: {', '.join(missing)}")
        recommendations.append(f"Try querying for {', '.join(matched_tickers)} specifically")
    
    if coverage == "minimal":
        gaps.append("No direct matches for query tickers")
        recommendations.append("Data may not exist for requested tickers/time period")
    
    if not has_json:
        gaps.append("No structured JSON data")
        recommendations.append("Only PDF data available - results may be limited")
    
    return {
        "has_data": True,
        "quality_score": round(relevance_score, 1),
        "coverage": coverage,
        "sources": {"pdf": has_pdf, "json": has_json},
        "tickers_found": list(tickers_found),
        "tickers_requested": list(query_tickers),
        "tickers_matched": list(matched_tickers),
        "gaps": gaps,
        "recommendations": recommendations
    }


def generate_enhanced_prompt(
    query: str,
    contexts: List[Dict[str, Any]],
    mode: str = "balanced",
    include_quality_analysis: bool = True,
    enrichment_text: str = "",
) -> str:
    """Generate enhanced prompt with quality analysis and mode-specific instructions."""
    
    system_prompt = generate_system_prompt(mode)
    context_block = generate_context_block(contexts)
    quality = analyze_data_quality(contexts, query)
    
    # Build quality section
    quality_section = ""
    if include_quality_analysis:
        quality_section = f"""
---
DATA QUALITY ASSESSMENT:
- Relevance Score: {quality['quality_score']}/100
- Coverage: {quality['coverage']}
- Sources: JSON={'Yes' if quality['sources']['json'] else 'No'}, PDF={'Yes' if quality['sources']['pdf'] else 'No'}
- Tickers Found: {', '.join(quality['tickers_found']) if quality['tickers_found'] else 'None'}
"""
        
        if quality['gaps']:
            quality_section += f"- Gaps: {', '.join(quality['gaps'])}\n"
        
        if quality['recommendations']:
            quality_section += f"- Suggestions: {', '.join(quality['recommendations'])}\n"
        
        quality_section += "---\n"
    
    # Mode-specific guidance
    mode_guidance = {
        "strict": "\n[MODE: STRICT - Use ONLY the data above, no inferences]\n",
        "balanced": "\n[MODE: BALANCED - Use data + reasonable connections, mark inferences]\n",
        "explorative": "\n[MODE: EXPLORATIVE - Broad analysis with confidence markers]\n"
    }.get(mode, "")
    
    enrichment_section = ""
    if enrichment_text:
        enrichment_section = f"""
{enrichment_text}
---
"""

    prompt = f"""{system_prompt}

{mode_guidance}
{quality_section}
CONTEXT INFORMATION:
{context_block}
---
{enrichment_section}
USER QUESTION: {query}

Provide your answer with appropriate confidence markers. If you cannot answer confidently, say so explicitly."""

    return prompt


def ask_enhanced(
    question: str,
    mode: str = "balanced",
    n_results: int = 5,
    include_quality_analysis: bool = True,
    use_hybrid_search: bool = True
) -> Dict[str, Any]:
    """
    Enhanced RAG query with mode selection and quality assessment.
    
    Args:
        question: User question
        mode: Response mode - "strict", "balanced", or "explorative"
        n_results: Number of context chunks to retrieve
        include_quality_analysis: Include data quality in prompt
        use_hybrid_search: Use hybrid search with ticker extraction
    
    Returns:
        Dict with answer, quality assessment, and metadata
    """
    # Validate mode
    if mode not in RESPONSE_MODES:
        mode = "balanced"
    
    mode_config = RESPONSE_MODES[mode]
    
    # Validate config
    errors = validate_config()
    if errors:
        return {
            "question": question,
            "answer": None,
            "sources": [],
            "quality": None,
            "success": False,
            "mode": mode,
            "error": "; ".join(errors),
            "enrichment": {},
        }
    
    # Check provider availability
    if LLM_PROVIDER == "ollama" and not check_ollama():
        return {
            "question": question,
            "answer": None,
            "sources": [],
            "quality": None,
            "success": False,
            "mode": mode,
            "error": f"Ollama is not running at {OLLAMA_BASE_URL}",
            "enrichment": {},
        }
    
    # Retrieve contexts
    if use_hybrid_search:
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
    
    # Analyze data quality
    quality = analyze_data_quality(contexts, question)
    
    # Handle no data case
    if not contexts:
        return {
            "question": question,
            "answer": "I couldn't find any relevant data for your question. " +
                     "This could be because:\n" +
                     "- The ticker/company isn't in our database\n" +
                     "- The data for that time period isn't available\n" +
                     "- The query might need to be more specific\n\n" +
                     "Try asking about a specific ticker like BBRI, BBCA, or GOTO.",
            "sources": [],
            "quality": quality,
            "success": True,
            "mode": mode,
            "error": None,
            "enrichment": {},
        }
    
    # Live enrichment from Stockbit
    tickers = extract_tickers(question)
    enrichment_data = enrich_tickers(tickers) if tickers else {}
    enrichment_text = format_enrichment_for_prompt(enrichment_data)

    # Generate enhanced prompt
    prompt = generate_enhanced_prompt(
        question, contexts, mode, include_quality_analysis,
        enrichment_text=enrichment_text,
    )
    
    # Get temperature from mode config
    temperature = mode_config["temperature"]
    
    # Call LLM
    if LLM_PROVIDER == "jatevo":
        response = ask_jatevo(prompt, temperature=temperature, max_tokens=4096)
    else:
        response = ask_ollama(prompt, temperature=temperature, max_tokens=2048)
    
    if not response['success']:
        return {
            "question": question,
            "answer": None,
            "sources": contexts,
            "quality": quality,
            "success": False,
            "mode": mode,
            "error": response['error'],
            "enrichment": enrichment_data,
        }
    
    # Format sources for response
    formatted_sources = []
    for ctx in contexts:
        meta = ctx['metadata']
        source_info = {
            'id': ctx.get('id', 'unknown'),
            'source': meta.get('source', 'unknown'),
            'text_preview': ctx['text'][:200] + '...',
            'distance': ctx['distance'],
            'relevance': round((1 - min(ctx['distance'], 1)) * 100, 1)
        }
        
        if meta.get('source') == 'ksei_json':
            source_info.update({
                'ticker': meta.get('ticker'),
                'date': meta.get('date'),
                'chunk_type': meta.get('chunk_type')
            })
        elif meta.get('source') == 'ksei_pdf':
            source_info.update({
                'filename': meta.get('filename'),
                'page_number': meta.get('page_number')
            })
        
        formatted_sources.append(source_info)
    
    return {
        "question": question,
        "answer": response['text'],
        "sources": formatted_sources,
        "quality": quality,
        "success": True,
        "mode": mode,
        "error": None,
        "usage": response.get('usage', {}),
        "enrichment": enrichment_data,
    }


def ask_jatevo(prompt: str, model: str = JATEVO_MODEL, temperature: float = 0.3, max_tokens: int = 4096) -> Dict[str, Any]:
    """Send prompt to Jatevo API."""
    if not JATEVO_API_KEY:
        return {"success": False, "text": None, "error": "JATEVO_API_KEY not configured"}
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JATEVO_API_KEY}"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
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
            choices = data.get('choices', [])
            if choices:
                content = choices[0].get('message', {}).get('content', '').strip()
                return {"success": True, "text": content, "error": None, "usage": data.get('usage', {})}
            return {"success": False, "text": None, "error": "No response content"}
        elif response.status_code == 401:
            return {"success": False, "text": None, "error": "Authentication failed"}
        else:
            return {"success": False, "text": None, "error": f"API error {response.status_code}: {response.text}"}
    
    except requests.exceptions.ConnectionError:
        return {"success": False, "text": None, "error": f"Cannot connect to Jatevo API"}
    except requests.exceptions.Timeout:
        return {"success": False, "text": None, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "text": None, "error": str(e)}


def ask_ollama(prompt: str, model: str = OLLAMA_MODEL, temperature: float = 0.3, max_tokens: int = 2048) -> Dict[str, Any]:
    """Send prompt to Ollama."""
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
            return {"success": True, "text": data.get('response', '').strip(), "error": None}
        else:
            return {"success": False, "text": None, "error": f"Ollama error {response.status_code}"}
    
    except requests.exceptions.ConnectionError:
        return {"success": False, "text": None, "error": "Cannot connect to Ollama"}
    except Exception as e:
        return {"success": False, "text": None, "error": str(e)}


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False
