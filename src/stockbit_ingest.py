"""
Ingest enrichment data from Stockbit API into ChromaDB.

Fetches company profiles, financial ratios, analyst consensus,
and major holders for tickers found in existing KSEI data.
Stores them as new chunk types alongside KSEI ownership chunks.
"""

import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from tqdm import tqdm

# Add parent dir so stockbit package is importable
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from embedder import embed_and_store, get_or_create_collection, get_stats
from config import STOCKBIT_TOKEN


def _get_stockbit_client():
    """Create a StockbitClient instance. Returns None if token not configured."""
    if not STOCKBIT_TOKEN:
        print("Warning: STOCKBIT_TOKEN not set. Stockbit ingestion skipped.")
        return None
    try:
        from stockbit import StockbitClient
        return StockbitClient(token=STOCKBIT_TOKEN)
    except Exception as e:
        print(f"Error creating StockbitClient: {e}")
        return None


def _fmt(value, suffix: str = "", default: str = "N/A") -> str:
    """Format a value for display, returning default if None."""
    if value is None:
        return default
    return f"{value}{suffix}"


def _fmt_market_cap(value) -> str:
    """Format market cap to human-readable IDR."""
    if value is None:
        return "N/A"
    try:
        v = float(value)
        if v >= 1e15:
            return f"Rp {v/1e12:,.0f} T"
        elif v >= 1e12:
            return f"Rp {v/1e12:,.1f} T"
        elif v >= 1e9:
            return f"Rp {v/1e9:,.0f} B"
        return f"Rp {v:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


def format_company_profile_chunk(info, profile) -> Tuple[str, Dict[str, Any]]:
    """
    Format company info + profile into a natural language chunk.

    Args:
        info: CompanyInfo object from stockbit client
        profile: CompanyProfile object from stockbit client

    Returns:
        (text, metadata) tuple ready for embedding
    """
    symbol = info.symbol or "UNKNOWN"
    name = info.name or getattr(profile, 'company_name', None) or symbol
    description = getattr(profile, 'description', None) or ""

    lines = [
        f"PROFIL PERUSAHAAN: {symbol} - {name}",
        f"Sektor: {_fmt(info.sector)}",
        f"Industri: {_fmt(info.industry)}",
        f"Market Cap: {_fmt_market_cap(info.market_cap)}",
        f"Tanggal Listing: {_fmt(info.listing_date)}",
        f"Jumlah Saham Beredar: {_fmt(info.shares_outstanding)}",
    ]

    if description:
        lines.append(f"Deskripsi: {description[:500]}")

    website = getattr(profile, 'website', None)
    if website:
        lines.append(f"Website: {website}")

    text = "\n".join(lines)
    metadata = {
        "source": "stockbit",
        "ticker": symbol,
        "issuer": name,
        "chunk_type": "company_profile",
        "sector": info.sector or "",
        "industry": info.industry or "",
    }
    return text, metadata


def format_financial_ratios_chunk(ticker: str, issuer_name: str, ratios) -> Tuple[str, Dict[str, Any]]:
    """
    Format key financial ratios into a natural language chunk.

    Args:
        ticker: Stock symbol
        issuer_name: Company name
        ratios: KeyRatios object from stockbit client

    Returns:
        (text, metadata) tuple ready for embedding
    """
    lines = [
        f"VALUASI & RASIO KEUANGAN: {ticker} - {issuer_name}",
        f"P/E Ratio: {_fmt(ratios.pe_ratio, 'x')}",
        f"P/B Ratio: {_fmt(ratios.pb_ratio, 'x')}",
        f"Dividend Yield: {_fmt(ratios.dividend_yield, '%')}",
        f"ROE (Return on Equity): {_fmt(ratios.roe, '%')}",
        f"ROA (Return on Assets): {_fmt(ratios.roa, '%')}",
    ]

    text = "\n".join(lines)
    metadata = {
        "source": "stockbit",
        "ticker": ticker,
        "issuer": issuer_name,
        "chunk_type": "financial_ratios",
    }
    return text, metadata


def format_analyst_consensus_chunk(ticker: str, issuer_name: str, consensus) -> Tuple[str, Dict[str, Any]]:
    """
    Format analyst consensus into a natural language chunk.

    Args:
        ticker: Stock symbol
        issuer_name: Company name
        consensus: AnalystConsensus object from stockbit client

    Returns:
        (text, metadata) tuple ready for embedding
    """
    recommendation = getattr(consensus, 'recommendation', None) or "N/A"
    total_buy = getattr(consensus, 'total_buy', None)
    total_hold = getattr(consensus, 'total_hold', None)
    total_sell = getattr(consensus, 'total_sell', None)
    avg_target = getattr(consensus, 'avg_price_target', None)

    lines = [
        f"KONSENSUS ANALIS: {ticker} - {issuer_name}",
        f"Rekomendasi: {recommendation}",
        f"Jumlah Analis Buy: {_fmt(total_buy)}",
        f"Jumlah Analis Hold: {_fmt(total_hold)}",
        f"Jumlah Analis Sell: {_fmt(total_sell)}",
        f"Rata-rata Target Harga: {_fmt(avg_target)}",
    ]

    text = "\n".join(lines)
    metadata = {
        "source": "stockbit",
        "ticker": ticker,
        "issuer": issuer_name,
        "chunk_type": "analyst_consensus",
    }
    return text, metadata


def format_major_holders_chunk(ticker: str, issuer_name: str, holders: List[Dict]) -> Tuple[str, Dict[str, Any]]:
    """
    Format major holders data from Stockbit into a natural language chunk.

    Args:
        ticker: Stock symbol
        issuer_name: Company name
        holders: List of holder dicts from stockbit client

    Returns:
        (text, metadata) tuple ready for embedding
    """
    lines = [
        f"PEMEGANG SAHAM UTAMA (Stockbit): {ticker} - {issuer_name}",
    ]

    if not holders:
        lines.append("No major holder data available from Stockbit.")
    else:
        for i, h in enumerate(holders[:10], 1):
            name = h.get("name", "Unknown")
            pct = h.get("percentage", 0)
            htype = h.get("type", "Unknown")
            lines.append(f"{i}. {name} - {pct}% ({htype})")

    text = "\n".join(lines)
    metadata = {
        "source": "stockbit",
        "ticker": ticker,
        "issuer": issuer_name,
        "chunk_type": "major_holders_stockbit",
    }
    return text, metadata


def get_ksei_tickers() -> List[str]:
    """Extract all unique tickers already ingested in ChromaDB from KSEI data."""
    collection = get_or_create_collection("ksei_data")
    results = collection.get(
        where={"source": "ksei_json"},
        include=["metadatas"],
        limit=10000,
    )
    tickers = set()
    for meta in results.get("metadatas", []):
        ticker = meta.get("ticker")
        if ticker:
            tickers.add(ticker)
    return sorted(tickers)


def ingest_stockbit_for_ticker(client, ticker: str) -> Dict[str, int]:
    """
    Fetch and ingest all Stockbit enrichment data for a single ticker.

    Returns dict with counts of chunks created per type.
    """
    chunks = []
    metadatas = []
    counts = {"company_profile": 0, "financial_ratios": 0, "analyst_consensus": 0, "major_holders_stockbit": 0}

    issuer_name = ticker

    # 1. Company info + profile
    try:
        info = client.company.get_info(ticker)
        profile = client.company.get_profile(ticker)
        text, meta = format_company_profile_chunk(info, profile)
        chunks.append(text)
        metadatas.append(meta)
        counts["company_profile"] = 1
        issuer_name = info.name or getattr(profile, 'company_name', None) or ticker
    except Exception as e:
        print(f"  [{ticker}] company info failed: {e}")

    # 2. Key ratios
    try:
        ratios = client.financials.get_key_ratios(ticker)
        text, meta = format_financial_ratios_chunk(ticker, issuer_name, ratios)
        chunks.append(text)
        metadatas.append(meta)
        counts["financial_ratios"] = 1
    except Exception as e:
        print(f"  [{ticker}] key ratios failed: {e}")

    # 3. Analyst consensus
    try:
        consensus = client.analyst.get_consensus(ticker)
        text, meta = format_analyst_consensus_chunk(ticker, issuer_name, consensus)
        chunks.append(text)
        metadatas.append(meta)
        counts["analyst_consensus"] = 1
    except Exception as e:
        print(f"  [{ticker}] analyst consensus failed: {e}")

    # 4. Major holders
    try:
        holders_raw = client.financials.get_major_holders(ticker)
        # Normalize: could be list of dicts or list of MajorHolder objects
        holders = []
        for h in (holders_raw or []):
            if isinstance(h, dict):
                holders.append(h)
            else:
                holders.append({
                    "name": getattr(h, "name", "Unknown"),
                    "percentage": getattr(h, "percentage", 0),
                    "type": getattr(h, "type", "Unknown"),
                })
        text, meta = format_major_holders_chunk(ticker, issuer_name, holders)
        chunks.append(text)
        metadatas.append(meta)
        counts["major_holders_stockbit"] = 1
    except Exception as e:
        print(f"  [{ticker}] major holders failed: {e}")

    # Store in ChromaDB
    if chunks:
        embed_and_store(chunks, metadatas, collection_name="ksei_data")

    return counts


def ingest_all_stockbit(tickers: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Ingest Stockbit enrichment data for all tickers.

    Args:
        tickers: Optional list of tickers. If None, auto-detects from KSEI data.

    Returns:
        Summary stats dict
    """
    client = _get_stockbit_client()
    if client is None:
        return {"error": "StockbitClient not available", "tickers_processed": 0}

    if tickers is None:
        tickers = get_ksei_tickers()

    if not tickers:
        print("No tickers found in KSEI data. Run KSEI ingestion first.")
        return {"error": "No tickers found", "tickers_processed": 0}

    print(f"Ingesting Stockbit data for {len(tickers)} tickers...")

    total_counts = {"company_profile": 0, "financial_ratios": 0, "analyst_consensus": 0, "major_holders_stockbit": 0}
    errors = []

    for ticker in tqdm(tickers, desc="Stockbit ingestion"):
        try:
            counts = ingest_stockbit_for_ticker(client, ticker)
            for k, v in counts.items():
                total_counts[k] += v
        except Exception as e:
            errors.append({"ticker": ticker, "error": str(e)})

    total_chunks = sum(total_counts.values())
    print(f"\nStockbit ingestion complete: {total_chunks} chunks from {len(tickers)} tickers")
    print(f"  Profiles: {total_counts['company_profile']}")
    print(f"  Ratios: {total_counts['financial_ratios']}")
    print(f"  Consensus: {total_counts['analyst_consensus']}")
    print(f"  Major holders: {total_counts['major_holders_stockbit']}")
    if errors:
        print(f"  Errors: {len(errors)}")

    return {
        "tickers_processed": len(tickers),
        "total_chunks": total_chunks,
        "counts": total_counts,
        "errors": errors,
    }


if __name__ == "__main__":
    result = ingest_all_stockbit()
    print(f"\nTotal documents in database: {get_stats()['document_count']}")
