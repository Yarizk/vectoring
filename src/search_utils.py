"""
Enhanced search utilities with ticker extraction and hybrid search.
"""

import re
from typing import List, Dict, Any, Optional
from embedder import search as base_search, get_or_create_collection

# Words that look like IDX tickers but are not
_EXCLUDE = {
    # English
    'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'ANY', 'CAN',
    'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM',
    'HIS', 'HOW', 'ITS', 'MAY', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WAY',
    'WHO', 'BOY', 'DID', 'EYE', 'SAW', 'SHE', 'TOO', 'USE', 'WHAT', 'WHEN',
    'WHERE', 'WHY', 'THAT', 'WITH', 'HAVE', 'THIS', 'WILL', 'YOUR', 'THEY',
    'BEEN', 'THEIR', 'SAID', 'EACH', 'WHICH', 'WOULD', 'THERE', 'COULD',
    'OTHER', 'AFTER', 'FIRST', 'NEVER', 'THESE', 'THINK', 'BEING', 'EVERY',
    'GREAT', 'MIGHT', 'SHALL', 'STILL', 'WHILE', 'THREE', 'FOUND', 'THOSE',
    'YOUNG', 'ABOUT', 'PRICE', 'STOCK', 'SHARE', 'FUND', 'BANK', 'COMPARE',
    'HIGH', 'LOW', 'BEST', 'MOST', 'LAST', 'YEAR', 'MONTH', 'WEEK', 'FROM',
    'INTO', 'OVER', 'ALSO', 'JUST', 'THAN', 'THEN', 'THEM', 'SOME', 'TIME',
    'VERY', 'WHEN', 'COME', 'BACK', 'KNOW', 'MAKE', 'GOOD', 'LOOK', 'ONLY',
    'COME', 'ITS', 'NOW', 'LONG', 'DOWN', 'DAY', 'DID', 'GET', 'SAME',
    'PE', 'PB', 'PS', 'EV', 'ROE', 'ROA', 'EPS', 'IDR', 'USD', 'YTD',
    'ETF', 'IPO', 'OJK', 'IDX', 'BEI', 'LQ',
    # Indonesian (2-letter)
    'DI', 'KE', 'DAN', 'YANG', 'UNTUK', 'DENGAN', 'DARI', 'INI', 'DALAM', 'PADA',
    'ADALAH', 'SEBAGAI', 'ATAU', 'JUGA', 'OLEH', 'SAHAM', 'BESAR', 'KECIL',
    'TERBESAR', 'PEMEGANG', 'PEMILIK', 'APA', 'SIAPA', 'BAGAIMANA', 'KAPAN',
    'DIMANA', 'MENGAPA', 'BERAPA', 'ASING', 'LOKAL', 'TOTAL', 'SEKTOR',
    'BULAN', 'TAHUN', 'MINGGU', 'LABA', 'RUGI', 'TREN', 'DATA', 'HARGA',
    'PASAR', 'NILAI', 'MODAL', 'UTANG', 'ASET', 'BELI', 'JUAL', 'NAIK',
    'TURUN', 'PERUBAHAN', 'KEPEMILIKAN', 'INSTITUSI', 'INDIVIDU', 'ASING',
    'REKOMENDASI', 'ANALIS', 'TARGET', 'DIVIDEN', 'KUARTAL', 'TAHUNAN',
    'TERTINGGI', 'TERENDAH', 'TERBAIK', 'TERBURUK', 'TERKECIL', 'TERBARU',
    'APAKAH', 'PERNAH', 'SUDAH', 'BELUM', 'MASIH', 'SAJA', 'SEPERTI',
    'KINERJA', 'PERFORMA', 'PENDAPATAN', 'KEUNTUNGAN', 'INVESTOR',
    'AKSI', 'MANA', 'DANA', 'HARI', 'TAHU', 'ATAS', 'ADA', 'NYA', 'KAN',
    'SAAT', 'INI', 'EX', 'DATE', 'KINI', 'TREN', 'SINI', 'BARU',
}

# Superlative/comparative keywords that signal a cross-stock screening query
# Keywords that signal market/financial data queries
_MARKET_SIGNALS = {
    # Company profile
    'bisnis', 'profil', 'profile', 'deskripsi', 'tentang perusahaan',
    # Price
    'harga', 'price', 'close', 'open', 'volume', 'saham',
    # Foreign flow (net_foreign in market_price)
    'aliran', 'flow', 'net foreign',
    # Ratios
    'pe', 'pb', 'roe', 'roa', 'eps', 'ratio', 'rasio', 'yield', 'dividend',
    'dividen', 'valuasi', 'valuation', 'earnings',
    # Financials
    'pendapatan', 'revenue', 'laba', 'profit', 'rugi', 'loss', 'ebitda',
    'kuartal', 'quarter', 'q1', 'q2', 'q3', 'q4', 'laporan', 'keuangan',
    'finansial', 'financial', 'income', 'balance', 'cashflow', 'arus kas',
    # Performance
    'performa', 'performance', 'return', 'kinerja', 'ytd', 'year to date',
    'weekly', 'monthly', 'yearly', '52 week', '52w', 'high', 'low',
    '1w', '1m', '3m', '6m', '1y', '3y',
    # Analyst
    'analis', 'analyst', 'rekomendasi', 'recommendation', 'target', 'konsensus',
    'buy', 'sell', 'hold', 'beli', 'jual', 'upgrade', 'downgrade',
    # Corporate actions
    'dividen', 'dividend', 'split', 'rights', 'bonus', 'aksi korporasi',
    'corporate action', 'ex date', 'paydate',
}

# Keywords that signal KSEI ownership queries
_OWNERSHIP_SIGNALS = {
    'pemegang', 'holder', 'kepemilikan', 'ownership', 'investor',
    'institusi', 'institution', 'pemilik', 'owner',
    'punya', 'miliki', 'memiliki', 'dimiliki', 'memegang', 'dipegang',
    'dana pensiun', 'reksa dana', 'reksadana',
    'asing', 'foreign',  # kepemilikan asing / foreign ownership %
}


def _detect_query_type(query: str):
    """
    Returns: 'market', 'ownership', or 'both'
    """
    q = query.lower()
    has_market = any(sig in q for sig in _MARKET_SIGNALS)
    has_ownership = any(sig in q for sig in _OWNERSHIP_SIGNALS)
    if has_market and not has_ownership:
        return 'market'
    if has_ownership and not has_market:
        return 'ownership'
    return 'both'


_MARKET_CHUNK_TYPES = {
    "market_price", "market_ratios", "market_financials",
    "market_performance", "market_analyst", "market_actions", "market_company",
    "sbitools_fundamentals", "sbitools_financials", "sbitools_company",
}
_OWNERSHIP_CHUNK_TYPES = {"ticker_summary", "holder_focus", "pdf_page"}

# Per-chunk-type keyword signals for sub-type routing within market queries
_CHUNK_TYPE_SIGNALS: Dict[str, List[str]] = {
    "market_performance": [
        "performa", "performance", "kinerja harga", "return saham",
        "52 week", "52w", "ytd", "year to date", "pertumbuhan harga",
        "naik berapa", "turun berapa", "1w", "1m", "3m", "6m", "1y", "3y",
    ],
    "market_ratios": [
        "roe", "roa", "roic", "pe ratio", "pb ratio", "ev/ebitda",
        "valuasi", "valuation", "rasio keuangan", "financial ratio",
        "profitabilitas", "profitability", "earnings yield", "dividend yield",
        "price to earnings", "price to book",
    ],
    "market_financials": [
        "tren pendapatan", "revenue trend", "laba bersih", "net income",
        "net profit", "laba kotor", "gross profit", "kuartal terakhir",
        "quarterly", "laporan keuangan", "income statement",
        "q1 ", "q2 ", "q3 ", "q4 ", "ebitda", "tren laba",
        "eps", "earning per share", "laba per saham",
    ],
    "market_actions": [
        "aksi korporasi", "corporate action",
        "kapan dividen", "jadwal dividen", "ex date", "ex-date", "pay date",
        "stock split", "split saham", "rights issue", "rups", "bonus saham",
        "dividen terakhir", "dividen kapan",
    ],
    "market_analyst": [
        "rekomendasi", "recommendation", "konsensus", "consensus",
        "target harga", "target price", "analis", "analyst",
        "upgrade", "downgrade", "buy", "sell", "hold", "rating",
        "revisi estimasi",
    ],
    "market_price": [
        "harga saham", "stock price", "harga penutupan", "close price",
        "volume perdagangan", "net aliran asing", "net foreign flow",
        "aliran asing", "foreign flow", "harga sekarang", "harga hari ini",
        "bandingkan harga", "compare price",
    ],
    "market_company": [
        "profil perusahaan", "company profile", "tentang perusahaan",
        "bergerak di bidang", "sektor apa", "industri apa",
        "bisnis utama", "bisnis apa", "apa bisnis", "deskripsi perusahaan",
        "tentang", "latar belakang",
    ],
}


def _preferred_chunk_type(query: str) -> Optional[str]:
    """
    Score each market chunk type by how many of its signals appear in the query.
    Returns the top-scoring type, or None if no signals match.
    """
    q = query.lower()
    scores: Dict[str, int] = {}
    for ct, signals in _CHUNK_TYPE_SIGNALS.items():
        score = sum(1 for sig in signals if sig in q)
        if score > 0:
            scores[ct] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


_COMPARATIVE_SIGNALS = {
    'tertinggi', 'terendah', 'terbesar', 'terkecil', 'terbaik', 'terburuk',
    'termahal', 'termurah', 'terbanyak', 'tersedikit',
    'paling tinggi', 'paling rendah', 'paling banyak', 'paling sedikit',
    'paling murah', 'paling mahal',
    'highest', 'lowest', 'largest', 'smallest', 'best', 'worst', 'cheapest',
    'most', 'least', 'top', 'bottom',
    'mana yang', 'which stock', 'saham apa',
    'list', 'ranking', 'rank', 'daftar', 'urutan', 'bandingkan',
}


def is_comparative_query(query: str) -> bool:
    """
    Return True if the query asks for ranking/comparison across stocks.
    If a specific IDX ticker is mentioned, it's a single-stock query even if
    superlative words appear ("pemegang terbesar BBRI" = biggest holder of BBRI).
    """
    q = query.lower()
    if not any(sig in q for sig in _COMPARATIVE_SIGNALS):
        return False
    # If any real ticker is in the query, it's single-stock, not comparative
    tickers = extract_tickers(query)
    return len(tickers) == 0


def extract_tickers(text: str) -> List[str]:
    """
    Extract potential IDX stock tickers from text.
    IDX tickers: 2-4 uppercase letters. Returns list ordered by position.
    """
    pattern = r'\b([A-Z]{2,4})\b'
    # Preserve order of appearance so the "main" ticker comes first
    seen = set()
    result = []
    for m in re.finditer(pattern, text.upper()):
        word = m.group(1)
        if word not in _EXCLUDE and word not in seen:
            seen.add(word)
            result.append(word)
    return result


def extract_ticker_from_context(contexts: List[Dict]) -> Optional[str]:
    """Extract most common ticker from search results."""
    counts: Dict[str, int] = {}
    for ctx in contexts:
        t = ctx.get('metadata', {}).get('ticker')
        if t:
            counts[t] = counts.get(t, 0) + 1
    return max(counts, key=counts.get) if counts else None


def hybrid_search(
    query: str,
    n_results: int = 5,
    use_ticker_boost: bool = True,
) -> List[Dict[str, Any]]:
    """
    Hybrid search:
    1. Extract tickers from query (positional order, not set)
    2. For each ticker: semantic search within that ticker's chunks
    3. Supplement with PDF page results (no ticker metadata)
    4. Merge, deduplicate, sort by distance, return top n_results
    """
    tickers = extract_tickers(query) if use_ticker_boost else []

    query_type = _detect_query_type(query)

    if tickers and not is_comparative_query(query):
        all_results: List[Dict] = []
        seen_ids: set = set()
        preferred: Optional[str] = None

        # Per-ticker filtered search — fetch more than needed so good chunks aren't crowded out
        per_ticker = max(n_results * 3, 10)

        # Decide which chunk types to search based on query type
        if query_type == 'market':
            preferred = _preferred_chunk_type(query)

            # Helper: search one chunk type for all tickers
            def _search_ct(ct: str, n: int):
                for ticker in tickers[:3]:
                    try:
                        results = base_search(
                            query, n_results=n,
                            where={"$and": [{"ticker": {"$eq": ticker}}, {"chunk_type": {"$eq": ct}}]}
                        )
                        for r in results:
                            if r['id'] not in seen_ids:
                                seen_ids.add(r['id'])
                                all_results.append(r)
                    except Exception:
                        pass

            # Search preferred type first with 2× results
            if preferred:
                _search_ct(preferred, per_ticker * 2)

            # Search all other market chunk types as supplementary
            for ct in sorted(_MARKET_CHUNK_TYPES):
                if ct == preferred:
                    continue
                _search_ct(ct, per_ticker)

            # Supplement with ownership if very few market results
            if len(all_results) < n_results:
                for ticker in tickers[:3]:
                    filtered = base_search(query, n_results=3, where={"ticker": ticker})
                    for r in filtered:
                        if r['id'] not in seen_ids:
                            seen_ids.add(r['id'])
                            all_results.append(r)
        elif query_type == 'ownership':
            # Search ownership chunk types + pdf
            for ticker in tickers[:3]:
                for ct in ('ticker_summary', 'holder_focus'):
                    try:
                        filtered = base_search(
                            query, n_results=per_ticker,
                            where={"$and": [{"ticker": {"$eq": ticker}}, {"chunk_type": {"$eq": ct}}]}
                        )
                        for r in filtered:
                            if r['id'] not in seen_ids:
                                seen_ids.add(r['id'])
                                all_results.append(r)
                    except Exception:
                        pass
            # Add pdf_page results
            try:
                pdf_results = base_search(query, n_results=2, where={"chunk_type": "pdf_page"})
                for r in pdf_results:
                    if r['id'] not in seen_ids:
                        seen_ids.add(r['id'])
                        all_results.append(r)
            except Exception:
                pass
        else:
            # 'both' — search all chunks for this ticker (original behavior)
            for ticker in tickers[:3]:
                filtered = base_search(query, n_results=per_ticker, where={"ticker": ticker})
                for r in filtered:
                    if r['id'] not in seen_ids:
                        seen_ids.add(r['id'])
                        all_results.append(r)
            # Add pdf_page if sparse
            if len(all_results) < n_results:
                try:
                    pdf_results = base_search(query, n_results=2, where={"chunk_type": "pdf_page"})
                    for r in pdf_results:
                        if r['id'] not in seen_ids:
                            seen_ids.add(r['id'])
                            all_results.append(r)
                except Exception:
                    pass

        if all_results:
            if preferred and query_type == 'market':
                # Hard preference: preferred-type results first (sorted by dist),
                # then fill remaining slots from other types (sorted by dist).
                pref = [r for r in all_results if r.get('metadata', {}).get('chunk_type') == preferred]
                rest = [r for r in all_results if r.get('metadata', {}).get('chunk_type') != preferred]
                pref.sort(key=lambda x: x['distance'])
                rest.sort(key=lambda x: x['distance'])
                return (pref + rest)[:n_results]
            else:
                all_results.sort(key=lambda x: x['distance'])
                return all_results[:n_results]

    # Comparative query — try DuckDB ranking for market metrics
    if is_comparative_query(query):
        if query_type in ('market', 'both'):
            try:
                from market.comparative import run_comparative
                comp_text = run_comparative(query)
                if comp_text:
                    comp_result: Dict[str, Any] = {
                        'id': 'comparative_sql_result',
                        'text': comp_text,
                        'distance': 0.0,
                        'metadata': {
                            'chunk_type': 'comparative_sql',
                            'source': 'duckdb_ranking',
                        },
                    }
                    semantic = base_search(query, n_results=max(n_results - 1, 2))
                    return [comp_result] + [r for r in semantic if r['id'] != 'comparative_sql_result']
            except Exception:
                pass
        elif query_type in ('ownership', 'both'):
            # For ownership comparative, fetch many ticker_summary chunks
            # so the LLM can compare foreign ownership / holder counts across stocks.
            return base_search(query, n_results=min(n_results * 3, 15),
                               where={"chunk_type": "ticker_summary"})

    # Pure semantic fallback
    return base_search(query, n_results=n_results)


def search_with_expansion(
    query: str,
    n_results: int = 5,
) -> List[Dict[str, Any]]:
    """Search with bilingual query expansion."""
    expansions = {
        'holder': 'pemegang saham',
        'pemegang': 'holder',
        'foreign': 'asing',
        'asing': 'foreign',
        'ownership': 'kepemilikan',
        'kepemilikan': 'ownership',
        'largest': 'terbesar',
        'terbesar': 'largest',
    }
    query_lower = query.lower()
    expanded_queries = [query]
    for kw, syn in expansions.items():
        if kw in query_lower:
            expanded_queries.append(query_lower.replace(kw, syn))

    all_results: List[Dict] = []
    seen_ids: set = set()
    for q in expanded_queries[:3]:
        for r in hybrid_search(q, n_results=n_results):
            if r['id'] not in seen_ids:
                seen_ids.add(r['id'])
                all_results.append(r)

    all_results.sort(key=lambda x: x['distance'])
    return all_results[:n_results]


def comparative_search(query: str, n_results: int = 10) -> List[Dict[str, Any]]:
    """
    For ranking/comparison queries: skip ticker filter, return diverse results
    across many tickers so the LLM can compare them.
    """
    return base_search(query, n_results=n_results)


def get_ticker_summary(ticker: str, date: Optional[str] = None) -> Optional[str]:
    """Get full KSEI summary for a specific ticker."""
    collection = get_or_create_collection("ksei_data")
    where: Dict[str, Any] = {"$and": [
        {"ticker": {"$eq": ticker.upper()}},
        {"chunk_type": {"$eq": "ticker_summary"}},
    ]}
    if date:
        where["$and"].append({"date": {"$eq": date}})

    results = collection.get(where=where, limit=1)
    return results['documents'][0] if results['documents'] else None


def get_holder_info(holder_name: str) -> List[Dict[str, Any]]:
    """Search for information about a specific institutional holder."""
    collection = get_or_create_collection("ksei_data")
    results = collection.get(where={"chunk_type": "holder_focus"}, limit=200)
    holder_upper = holder_name.upper()
    return [
        {'text': doc, 'metadata': results['metadatas'][i]}
        for i, doc in enumerate(results['documents'])
        if holder_upper in doc.upper()
    ]
