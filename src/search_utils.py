"""
Enhanced search utilities with ticker extraction and hybrid search.
"""

import re
from typing import List, Dict, Any, Optional
from embedder import search as base_search, get_or_create_collection


def extract_tickers(text: str) -> List[str]:
    """
    Extract potential stock tickers from text.
    Indonesian stock tickers are 2-4 uppercase letters.
    """
    # Common words to exclude (not stock tickers)
    exclude_words = {
        'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'ANY', 'CAN',
        'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM',
        'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY',
        'WHO', 'BOY', 'DID', 'EYE', 'SAW', 'SHE', 'TOO', 'USE', 'DAN', 'YANG',
        'UNTUK', 'DENGAN', 'DARI', 'INI', 'DALAM', 'PADA', 'ADALAH', 'SEBAGAI',
        'ATAU', 'JUGA', 'OLEH', 'SAHAM', 'BESAR', 'TERBESAR', 'PEMEGANG', 'PEMILIK',
        'APA', 'SIAPA', 'BAGAIMANA', 'KAPAN', 'DIMANA', 'MENGAPA', 'COMPARE',
        'WHAT', 'WHEN', 'WHERE', 'WHO', 'WHY', 'HOW', 'PRICE', 'ABOUT', 'THAT',
        'WITH', 'HAVE', 'THIS', 'WILL', 'YOUR', 'THEY', 'BEEN', 'THEIR', 'SAID',
        'EACH', 'WHICH', 'WOULD', 'THERE', 'COULD', 'OTHER', 'AFTER', 'FIRST',
        'NEVER', 'THESE', 'THINK', 'WHERE', 'BEING', 'EVERY', 'GREAT', 'MIGHT',
        'SHALL', 'STILL', 'WHILE', 'THREE', 'FOUND', 'THOSE', 'WHILE', 'YOUNG'
    }
    
    # Find all potential tickers (2-5 uppercase letters)
    pattern = r'\b([A-Z]{2,5})\b'
    matches = re.findall(pattern, text.upper())
    
    # Filter out common words
    tickers = [m for m in matches if m not in exclude_words]
    
    return list(set(tickers))  # Remove duplicates


def extract_ticker_from_context(contexts: List[Dict]) -> Optional[str]:
    """Extract most common ticker from search results."""
    ticker_counts = {}
    for ctx in contexts:
        ticker = ctx.get('metadata', {}).get('ticker')
        if ticker:
            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
    
    if ticker_counts:
        return max(ticker_counts, key=ticker_counts.get)
    return None


def hybrid_search(
    query: str,
    n_results: int = 5,
    use_ticker_boost: bool = True
) -> List[Dict[str, Any]]:
    """
    Hybrid search that:
    1. Extracts tickers from query
    2. Performs metadata-filtered search if ticker found
    3. Falls back to semantic search
    4. Reranks results by relevance
    """
    tickers = extract_tickers(query)
    
    if use_ticker_boost and tickers:
        # Try each ticker in order of appearance
        for ticker in tickers:
            # First try exact ticker match
            filtered_results = base_search(
                query, 
                n_results=n_results,
                where={"ticker": ticker}
            )
            if filtered_results:
                return filtered_results
    
    # Fallback to pure semantic search
    return base_search(query, n_results=n_results)


def search_with_expansion(
    query: str,
    n_results: int = 5,
    expand_with_summary: bool = True
) -> List[Dict[str, Any]]:
    """
    Search with query expansion for better recall.
    
    Expands queries like:
    - "BBCA holder" -> includes "pemegang saham BBCA"
    - "foreign ownership" -> includes "kepemilikan asing"
    """
    # Synonym mappings for Indonesian/English
    expansions = {
        'holder': ['pemegang saham', 'pemilik', 'investor'],
        'pemegang': ['holder', 'pemilik', 'investor'],
        'foreign': ['asing', 'asingnya'],
        'asing': ['foreign', 'international'],
        'ownership': ['kepemilikan', 'porsi', 'saham'],
        'kepemilikan': ['ownership', 'porsi'],
        'largest': ['terbesar', 'paling besar', 'majoritas'],
        'terbesar': ['largest', 'biggest', 'majority'],
    }
    
    # Check if query contains keywords to expand
    query_lower = query.lower()
    expanded_queries = [query]
    
    for keyword, synonyms in expansions.items():
        if keyword in query_lower:
            for synonym in synonyms:
                expanded = query_lower.replace(keyword, synonym)
                if expanded != query_lower:
                    expanded_queries.append(expanded)
    
    # Search with each expanded query and combine results
    all_results = []
    seen_ids = set()
    
    for q in expanded_queries[:3]:  # Limit to first 3 variations
        results = hybrid_search(q, n_results=n_results)
        for r in results:
            if r['id'] not in seen_ids:
                seen_ids.add(r['id'])
                all_results.append(r)
    
    # Sort by distance (lower is better)
    all_results.sort(key=lambda x: x['distance'])
    
    return all_results[:n_results]


def get_ticker_summary(ticker: str, date: Optional[str] = None) -> Optional[str]:
    """Get full summary for a specific ticker."""
    collection = get_or_create_collection("ksei_data")
    
    # ChromaDB requires $and operator for multiple conditions
    where_filter = {"$and": [
        {"ticker": {"$eq": ticker.upper()}},
        {"chunk_type": {"$eq": "ticker_summary"}}
    ]}
    
    if date:
        where_filter["$and"].append({"date": {"$eq": date}})
    
    results = collection.get(
        where=where_filter,
        limit=1
    )
    
    if results['documents']:
        return results['documents'][0]
    return None


def get_holder_info(holder_name: str) -> List[Dict[str, Any]]:
    """Search for information about a specific holder."""
    collection = get_or_create_collection("ksei_data")
    
    # Search in holder_name field
    results = collection.get(
        where={"chunk_type": "holder_focus"},
        limit=100
    )
    
    matching = []
    holder_upper = holder_name.upper()
    
    for i, doc in enumerate(results['documents']):
        if holder_upper in doc.upper():
            matching.append({
                'text': doc,
                'metadata': results['metadatas'][i]
            })
    
    return matching
