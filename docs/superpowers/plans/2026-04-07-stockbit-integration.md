# Stockbit Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the existing `stockbit/` API library into the KSEI RAG system to enrich ownership data with company profiles, financial ratios, analyst consensus (embedded into ChromaDB) and live market data like foreign flow, prices, and corporate actions (fetched on-demand at query time).

**Architecture:** Two-layer context injection. **Layer 1 (static):** A new `stockbit_ingest.py` periodically fetches company info, key ratios, analyst consensus, and major holders from the Stockbit API and embeds them as new chunk types in ChromaDB alongside existing KSEI data. **Layer 2 (dynamic):** A new `stockbit_enricher.py` fetches live data (foreign flow, price performance, recent corp actions) at query time for detected tickers and injects it into the LLM prompt as a separate "LIVE MARKET DATA" section. The RAG pipeline in `rag_enhanced.py` is modified to call the enricher after retrieval and before prompt assembly. Jatevo (qwen3.5-plus) is the primary LLM provider; Ollama is fallback. A new `/api/ticker/{symbol}` endpoint exposes enrichment data to the frontend, and the frontend gets a `MarketContext` card that displays live data alongside AI answers.

**Tech Stack:** Python 3.10+, FastAPI, ChromaDB, sentence-transformers, Stockbit Python client (`stockbit/` local lib), React 19, Zustand, TypeScript, Tailwind CSS, Vite 6.

---

## File Structure

### New Files (Backend)

| File | Responsibility |
|---|---|
| `src/stockbit_ingest.py` | Periodic ingestion: fetch company profiles, ratios, consensus, major holders from Stockbit API and embed into ChromaDB as new chunk types |
| `src/stockbit_enricher.py` | Live query-time enrichment: fetch foreign flow, price performance, recent corp actions for detected tickers. Returns formatted text for prompt injection + structured data for API response |
| `tests/test_stockbit_ingest.py` | Tests for Stockbit ingestion formatting and chunking logic |
| `tests/test_stockbit_enricher.py` | Tests for live enrichment formatting and graceful failure handling |
| `tests/test_rag_integration.py` | Tests that the modified RAG pipeline correctly merges static + live context |
| `tests/conftest.py` | Shared test fixtures (mock Stockbit client, mock ChromaDB) |

### Modified Files (Backend)

| File | What Changes |
|---|---|
| `src/config.py` | Add `STOCKBIT_TOKEN` env var |
| `src/rag_enhanced.py` | Call `stockbit_enricher` after retrieval, inject live context into prompt, include enrichment in response |
| `src/api.py` | Add `/api/ticker/{symbol}` endpoint, modify `/ask` response to include enrichment data |
| `.env.example` | Add `STOCKBIT_TOKEN` placeholder |
| `requirements.txt` | Add `pydantic-settings>=2.0.0` (needed by stockbit lib) |

### New Files (Frontend)

| File | Responsibility |
|---|---|
| `frontend/src/components/chat/MarketContext.tsx` | Card displayed in AI message showing live price, foreign flow, analyst consensus for detected tickers |
| `frontend/src/types/enrichment.ts` | TypeScript types for enrichment API response |

### Modified Files (Frontend)

| File | What Changes |
|---|---|
| `frontend/src/components/chat/AIMessage.tsx` | Render `MarketContext` card when enrichment data is present |
| `frontend/src/types/api.ts` | Add enrichment fields to `AskResponse` |
| `frontend/src/types/index.ts` | Export new enrichment types |
| `frontend/src/lib/api.ts` | Implement the `getMarketData` and `getBatchMarketData` placeholder functions |

---

## Task 1: Config — Add Stockbit Token

**Files:**
- Modify: `src/config.py`
- Modify: `.env.example`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_config.py`:

```python
"""Tests for config module."""
import os
import importlib


def test_stockbit_token_loaded_from_env(monkeypatch):
    """STOCKBIT_TOKEN should be accessible from config."""
    monkeypatch.setenv("STOCKBIT_TOKEN", "test_token_123")
    # Force reimport to pick up new env
    import src.config as config_mod
    importlib.reload(config_mod)
    assert config_mod.STOCKBIT_TOKEN == "test_token_123"


def test_stockbit_token_defaults_to_empty(monkeypatch):
    """STOCKBIT_TOKEN should default to empty string if not set."""
    monkeypatch.delenv("STOCKBIT_TOKEN", raising=False)
    import src.config as config_mod
    importlib.reload(config_mod)
    assert config_mod.STOCKBIT_TOKEN == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd d:/Kuliah/Project/vectoring && python -m pytest tests/test_config.py -v`
Expected: FAIL — `STOCKBIT_TOKEN` not defined in `src/config.py`

- [ ] **Step 3: Add STOCKBIT_TOKEN to config.py**

In `src/config.py`, after the line `JATEVO_MODEL = os.getenv("JATEVO_MODEL", "qwen3.5-plus")` (line 22), add:

```python
# Stockbit API Configuration
STOCKBIT_TOKEN = os.getenv("STOCKBIT_TOKEN", "")
```

- [ ] **Step 4: Add to .env.example**

Append to `.env.example` after the `API_PORT=8000` line:

```
# Stockbit API Configuration
STOCKBIT_TOKEN=your_stockbit_token_here
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd d:/Kuliah/Project/vectoring && python -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/test_config.py src/config.py .env.example
git commit -m "feat: add STOCKBIT_TOKEN to config"
```

---

## Task 2: conftest.py — Shared Test Fixtures

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Create shared test fixtures**

Create `tests/conftest.py`:

```python
"""Shared test fixtures for stockbit integration tests."""
import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace


@pytest.fixture
def mock_company_info():
    """Mock stockbit CompanyInfo response."""
    return SimpleNamespace(
        symbol="BBCA",
        name="Bank Central Asia Tbk",
        sector="Financials",
        industry="Banks",
        market_cap=1200000000000000,
        listing_date="2000-05-31",
        shares_outstanding=24655000000,
    )


@pytest.fixture
def mock_company_profile():
    """Mock stockbit CompanyProfile response."""
    return SimpleNamespace(
        symbol="BBCA",
        company_name="Bank Central Asia Tbk",
        description="PT Bank Central Asia Tbk provides commercial banking services.",
        sector="Financials",
        industry="Banks",
        website="https://www.bca.co.id",
        employees=25000,
    )


@pytest.fixture
def mock_key_ratios():
    """Mock stockbit KeyRatios response."""
    return SimpleNamespace(
        symbol="BBCA",
        pe_ratio=22.5,
        pb_ratio=4.8,
        dividend_yield=2.1,
        roe=21.3,
        roa=3.5,
    )


@pytest.fixture
def mock_analyst_consensus():
    """Mock stockbit AnalystConsensus response."""
    return SimpleNamespace(
        symbol="BBCA",
        recommendation="Buy",
        total_buy=18,
        total_sell=1,
        total_hold=5,
        avg_price_target=11500,
    )


@pytest.fixture
def mock_major_holders():
    """Mock stockbit major holders response."""
    return [
        {"name": "PT Dwimuria Investama Mandiri", "shares": 13209561000, "percentage": 53.58, "type": "Institution"},
        {"name": "Norges Bank", "shares": 504000000, "percentage": 2.04, "type": "Foreign"},
    ]


@pytest.fixture
def mock_foreign_flow():
    """Mock stockbit ForeignDomesticFlow response."""
    return SimpleNamespace(
        symbol="BBCA",
        data={
            "foreign_buy": 150000000000,
            "foreign_sell": 105000000000,
            "domestic_buy": 200000000000,
            "domestic_sell": 245000000000,
        },
    )


@pytest.fixture
def mock_price_performance():
    """Mock stockbit PricePerformance response."""
    return SimpleNamespace(
        symbol="BBCA",
        performance_1w=1.2,
        performance_1m=3.5,
        performance_3m=8.1,
        performance_6m=12.4,
        performance_ytd=15.0,
        performance_1y=22.3,
    )


@pytest.fixture
def mock_corp_actions():
    """Mock stockbit corporate actions response."""
    return [
        SimpleNamespace(
            symbol="BBCA",
            action_type="dividend",
            announcement_date="2026-03-15",
            ex_date="2026-04-10",
            description="Cash Dividend Rp 250 per share",
        ),
    ]


@pytest.fixture
def mock_stockbit_client(
    mock_company_info, mock_company_profile, mock_key_ratios,
    mock_analyst_consensus, mock_major_holders, mock_foreign_flow,
    mock_price_performance, mock_corp_actions,
):
    """Fully mocked StockbitClient."""
    client = MagicMock()
    client.company.get_info.return_value = mock_company_info
    client.company.get_profile.return_value = mock_company_profile
    client.financials.get_key_ratios.return_value = mock_key_ratios
    client.analyst.get_consensus.return_value = mock_analyst_consensus
    client.financials.get_major_holders.return_value = mock_major_holders
    client.financials.get_foreign_domestic_flow.return_value = mock_foreign_flow
    client.quotes.get_price_performance.return_value = mock_price_performance
    client.corporate_actions.get_by_symbol.return_value = mock_corp_actions
    return client
```

- [ ] **Step 2: Verify fixtures load**

Run: `cd d:/Kuliah/Project/vectoring && python -m pytest tests/conftest.py --co -v`
Expected: "no tests ran" (conftest has no tests, but should parse without errors)

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add shared fixtures for stockbit integration tests"
```

---

## Task 3: stockbit_ingest.py — Periodic Stockbit Data Ingestion

This is the largest task. It fetches company profiles, financial ratios, analyst consensus, and major holders from the Stockbit API, formats them as natural language chunks, and stores them in ChromaDB.

**Files:**
- Create: `src/stockbit_ingest.py`
- Test: `tests/test_stockbit_ingest.py`

- [ ] **Step 1: Write tests for formatting functions**

Create `tests/test_stockbit_ingest.py`:

```python
"""Tests for Stockbit data ingestion into ChromaDB."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from stockbit_ingest import (
    format_company_profile_chunk,
    format_financial_ratios_chunk,
    format_analyst_consensus_chunk,
    format_major_holders_chunk,
)


def test_format_company_profile_chunk(mock_company_info, mock_company_profile):
    text, metadata = format_company_profile_chunk(mock_company_info, mock_company_profile)

    assert "BBCA" in text
    assert "Bank Central Asia" in text
    assert "Financials" in text
    assert "Banks" in text
    assert metadata["source"] == "stockbit"
    assert metadata["ticker"] == "BBCA"
    assert metadata["chunk_type"] == "company_profile"


def test_format_company_profile_chunk_handles_none_fields():
    """Should handle None fields gracefully."""
    from types import SimpleNamespace
    info = SimpleNamespace(symbol="TEST", name=None, sector=None, industry=None,
                          market_cap=None, listing_date=None, shares_outstanding=None)
    profile = SimpleNamespace(symbol="TEST", company_name=None, description=None,
                             sector=None, industry=None, website=None, employees=None)
    text, metadata = format_company_profile_chunk(info, profile)
    assert "TEST" in text
    assert metadata["ticker"] == "TEST"


def test_format_financial_ratios_chunk(mock_key_ratios):
    text, metadata = format_financial_ratios_chunk("BBCA", "Bank Central Asia Tbk", mock_key_ratios)

    assert "P/E" in text
    assert "22.5" in text
    assert "ROE" in text
    assert "21.3" in text
    assert metadata["source"] == "stockbit"
    assert metadata["chunk_type"] == "financial_ratios"


def test_format_financial_ratios_chunk_handles_none():
    from types import SimpleNamespace
    ratios = SimpleNamespace(symbol="TEST", pe_ratio=None, pb_ratio=None,
                            dividend_yield=None, roe=None, roa=None)
    text, metadata = format_financial_ratios_chunk("TEST", "Test Corp", ratios)
    assert "TEST" in text
    assert "N/A" in text


def test_format_analyst_consensus_chunk(mock_analyst_consensus):
    text, metadata = format_analyst_consensus_chunk("BBCA", "Bank Central Asia Tbk", mock_analyst_consensus)

    assert "18" in text  # total_buy
    assert "Buy" in text or "buy" in text.lower()
    assert "11500" in text or "11,500" in text
    assert metadata["chunk_type"] == "analyst_consensus"


def test_format_major_holders_chunk(mock_major_holders):
    text, metadata = format_major_holders_chunk("BBCA", "Bank Central Asia Tbk", mock_major_holders)

    assert "Dwimuria" in text
    assert "53.58" in text
    assert "Norges" in text
    assert metadata["chunk_type"] == "major_holders_stockbit"


def test_format_major_holders_chunk_empty_list():
    text, metadata = format_major_holders_chunk("TEST", "Test Corp", [])
    assert "TEST" in text
    assert "No major holder" in text or metadata["chunk_type"] == "major_holders_stockbit"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd d:/Kuliah/Project/vectoring && python -m pytest tests/test_stockbit_ingest.py -v`
Expected: FAIL — `stockbit_ingest` module not found

- [ ] **Step 3: Implement stockbit_ingest.py**

Create `src/stockbit_ingest.py`:

```python
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
    name = info.name or profile.company_name or symbol
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

    # 1. Company info + profile
    try:
        info = client.company.get_info(ticker)
        profile = client.company.get_profile(ticker)
        text, meta = format_company_profile_chunk(info, profile)
        chunks.append(text)
        metadatas.append(meta)
        counts["company_profile"] = 1
    except Exception as e:
        print(f"  [{ticker}] company info failed: {e}")

    # Get issuer name for other chunks
    issuer_name = ""
    try:
        issuer_name = info.name or profile.company_name or ticker
    except Exception:
        issuer_name = ticker

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd d:/Kuliah/Project/vectoring && python -m pytest tests/test_stockbit_ingest.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/stockbit_ingest.py tests/test_stockbit_ingest.py
git commit -m "feat: add stockbit periodic ingestion for company profiles, ratios, consensus, holders"
```

---

## Task 4: stockbit_enricher.py — Live Query-Time Enrichment

**Files:**
- Create: `src/stockbit_enricher.py`
- Test: `tests/test_stockbit_enricher.py`

- [ ] **Step 1: Write tests for enrichment functions**

Create `tests/test_stockbit_enricher.py`:

```python
"""Tests for live Stockbit query-time enrichment."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import MagicMock, patch
from stockbit_enricher import (
    format_foreign_flow,
    format_price_performance,
    format_corp_actions,
    enrich_tickers,
    format_enrichment_for_prompt,
)


def test_format_foreign_flow(mock_foreign_flow):
    result = format_foreign_flow("BBCA", mock_foreign_flow)

    assert result is not None
    assert result["ticker"] == "BBCA"
    assert "foreign_net" in result
    # 150B buy - 105B sell = 45B net
    assert result["foreign_net"] == 150000000000 - 105000000000


def test_format_foreign_flow_none():
    """Should return None when flow data is unavailable."""
    result = format_foreign_flow("TEST", None)
    assert result is None


def test_format_price_performance(mock_price_performance):
    result = format_price_performance("BBCA", mock_price_performance)

    assert result["ticker"] == "BBCA"
    assert result["performance_1m"] == 3.5
    assert result["performance_1y"] == 22.3


def test_format_price_performance_none():
    result = format_price_performance("TEST", None)
    assert result is None


def test_format_corp_actions(mock_corp_actions):
    result = format_corp_actions("BBCA", mock_corp_actions)

    assert len(result) == 1
    assert result[0]["action_type"] == "dividend"
    assert "250" in result[0]["description"]


def test_format_corp_actions_empty():
    result = format_corp_actions("TEST", [])
    assert result == []


def test_format_enrichment_for_prompt():
    """Test the text block generated for LLM prompt injection."""
    enrichment = {
        "BBCA": {
            "foreign_flow": {"ticker": "BBCA", "foreign_net": 45000000000},
            "price_performance": {"ticker": "BBCA", "performance_1m": 3.5, "performance_1y": 22.3,
                                  "performance_1w": 1.2, "performance_3m": 8.1,
                                  "performance_ytd": 15.0, "performance_6m": 12.4},
            "corp_actions": [{"action_type": "dividend", "description": "Cash Dividend Rp 250",
                             "ex_date": "2026-04-10"}],
        }
    }
    text = format_enrichment_for_prompt(enrichment)

    assert "BBCA" in text
    assert "LIVE MARKET DATA" in text
    assert "45" in text  # foreign net in billions
    assert "3.5" in text  # 1m performance


def test_format_enrichment_for_prompt_empty():
    text = format_enrichment_for_prompt({})
    assert text == ""


@patch("stockbit_enricher._get_stockbit_client")
def test_enrich_tickers_returns_structured_data(mock_get_client, mock_stockbit_client):
    """enrich_tickers should return structured data per ticker."""
    mock_get_client.return_value = mock_stockbit_client
    result = enrich_tickers(["BBCA"])

    assert "BBCA" in result
    assert "foreign_flow" in result["BBCA"]
    assert "price_performance" in result["BBCA"]
    assert "corp_actions" in result["BBCA"]


@patch("stockbit_enricher._get_stockbit_client")
def test_enrich_tickers_graceful_on_api_error(mock_get_client):
    """Should return empty enrichment if API fails, not raise."""
    client = MagicMock()
    client.financials.get_foreign_domestic_flow.side_effect = Exception("API down")
    client.quotes.get_price_performance.side_effect = Exception("API down")
    client.corporate_actions.get_by_symbol.side_effect = Exception("API down")
    mock_get_client.return_value = client

    result = enrich_tickers(["BBCA"])
    # Should not raise — returns dict with None values
    assert "BBCA" in result
    assert result["BBCA"]["foreign_flow"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd d:/Kuliah/Project/vectoring && python -m pytest tests/test_stockbit_enricher.py -v`
Expected: FAIL — `stockbit_enricher` module not found

- [ ] **Step 3: Implement stockbit_enricher.py**

Create `src/stockbit_enricher.py`:

```python
"""
Live query-time enrichment from Stockbit API.

Fetches real-time data (foreign flow, price performance, corporate actions)
for tickers detected in user queries. This data is NOT embedded in ChromaDB —
it's fetched fresh and injected directly into the LLM prompt.
"""

import os
import sys
from typing import List, Dict, Any, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import STOCKBIT_TOKEN

# Cache the client instance to reuse connections
_client_instance = None


def _get_stockbit_client():
    """Get or create a cached StockbitClient instance."""
    global _client_instance
    if _client_instance is not None:
        return _client_instance
    if not STOCKBIT_TOKEN:
        return None
    try:
        from stockbit import StockbitClient
        _client_instance = StockbitClient(token=STOCKBIT_TOKEN)
        return _client_instance
    except Exception:
        return None


def format_foreign_flow(ticker: str, flow) -> Optional[Dict[str, Any]]:
    """Extract and format foreign flow data."""
    if flow is None:
        return None
    data = getattr(flow, 'data', None)
    if not data or not isinstance(data, dict):
        return None
    foreign_buy = data.get("foreign_buy", 0) or 0
    foreign_sell = data.get("foreign_sell", 0) or 0
    return {
        "ticker": ticker,
        "foreign_buy": foreign_buy,
        "foreign_sell": foreign_sell,
        "foreign_net": foreign_buy - foreign_sell,
    }


def format_price_performance(ticker: str, perf) -> Optional[Dict[str, Any]]:
    """Extract and format price performance data."""
    if perf is None:
        return None
    return {
        "ticker": ticker,
        "performance_1w": getattr(perf, 'performance_1w', None),
        "performance_1m": getattr(perf, 'performance_1m', None),
        "performance_3m": getattr(perf, 'performance_3m', None),
        "performance_6m": getattr(perf, 'performance_6m', None),
        "performance_ytd": getattr(perf, 'performance_ytd', None),
        "performance_1y": getattr(perf, 'performance_1y', None),
    }


def format_corp_actions(ticker: str, actions) -> List[Dict[str, Any]]:
    """Extract and format recent corporate actions."""
    if not actions:
        return []
    result = []
    for a in actions[:5]:  # Limit to 5 most recent
        result.append({
            "ticker": ticker,
            "action_type": getattr(a, 'action_type', None) or "unknown",
            "description": getattr(a, 'description', None) or "",
            "ex_date": getattr(a, 'ex_date', None),
            "announcement_date": getattr(a, 'announcement_date', None),
        })
    return result


def _fmt_idr(value) -> str:
    """Format IDR value to human-readable billions/trillions."""
    if value is None:
        return "N/A"
    try:
        v = float(value)
        if abs(v) >= 1e12:
            return f"Rp {v/1e12:,.1f}T"
        elif abs(v) >= 1e9:
            return f"Rp {v/1e9:,.1f}B"
        elif abs(v) >= 1e6:
            return f"Rp {v/1e6:,.0f}M"
        return f"Rp {v:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


def format_enrichment_for_prompt(enrichment: Dict[str, Dict]) -> str:
    """
    Format all enrichment data into a text block for LLM prompt injection.

    Args:
        enrichment: Dict mapping ticker -> {foreign_flow, price_performance, corp_actions}

    Returns:
        Formatted text block, or empty string if no data
    """
    if not enrichment:
        return ""

    sections = []
    for ticker, data in enrichment.items():
        lines = [f"--- {ticker} ---"]

        # Foreign flow
        flow = data.get("foreign_flow")
        if flow:
            net = flow.get("foreign_net", 0)
            direction = "Net Buy" if net > 0 else "Net Sell"
            lines.append(f"Foreign Flow: {direction} {_fmt_idr(abs(net))}")

        # Price performance
        perf = data.get("price_performance")
        if perf:
            parts = []
            for period, key in [("1W", "performance_1w"), ("1M", "performance_1m"),
                                ("3M", "performance_3m"), ("YTD", "performance_ytd"),
                                ("1Y", "performance_1y")]:
                val = perf.get(key)
                if val is not None:
                    sign = "+" if val > 0 else ""
                    parts.append(f"{period}: {sign}{val}%")
            if parts:
                lines.append(f"Price Performance: {', '.join(parts)}")

        # Corp actions
        actions = data.get("corp_actions", [])
        if actions:
            lines.append("Recent Corporate Actions:")
            for a in actions:
                desc = a.get("description", "")
                ex = a.get("ex_date", "")
                lines.append(f"  - {desc}" + (f" (ex-date: {ex})" if ex else ""))

        if len(lines) > 1:  # More than just the header
            sections.append("\n".join(lines))

    if not sections:
        return ""

    return "LIVE MARKET DATA (from Stockbit, real-time):\n\n" + "\n\n".join(sections)


def enrich_tickers(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch live enrichment data for a list of tickers.

    Args:
        tickers: List of stock symbols to enrich

    Returns:
        Dict mapping ticker -> {foreign_flow, price_performance, corp_actions}
        Each value can be None if the API call failed.
    """
    client = _get_stockbit_client()
    if client is None:
        return {}

    result = {}
    for ticker in tickers[:5]:  # Limit to 5 tickers to avoid slow queries
        ticker_data = {
            "foreign_flow": None,
            "price_performance": None,
            "corp_actions": [],
        }

        # Foreign flow
        try:
            flow_raw = client.financials.get_foreign_domestic_flow(ticker)
            ticker_data["foreign_flow"] = format_foreign_flow(ticker, flow_raw)
        except Exception:
            pass

        # Price performance
        try:
            perf_raw = client.quotes.get_price_performance(ticker)
            ticker_data["price_performance"] = format_price_performance(ticker, perf_raw)
        except Exception:
            pass

        # Corporate actions
        try:
            actions_raw = client.corporate_actions.get_by_symbol(ticker)
            ticker_data["corp_actions"] = format_corp_actions(ticker, actions_raw)
        except Exception:
            pass

        result[ticker] = ticker_data

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd d:/Kuliah/Project/vectoring && python -m pytest tests/test_stockbit_enricher.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/stockbit_enricher.py tests/test_stockbit_enricher.py
git commit -m "feat: add live stockbit enrichment for foreign flow, price perf, corp actions"
```

---

## Task 5: Wire Enrichment into RAG Pipeline

**Files:**
- Modify: `src/rag_enhanced.py:250-401` (the `ask_enhanced` function and `generate_enhanced_prompt`)
- Test: `tests/test_rag_integration.py`

- [ ] **Step 1: Write integration test**

Create `tests/test_rag_integration.py`:

```python
"""Tests for RAG pipeline integration with Stockbit enrichment."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import patch, MagicMock
from rag_enhanced import generate_enhanced_prompt


def test_prompt_includes_live_data_section():
    """When enrichment_text is provided, prompt should contain LIVE MARKET DATA section."""
    contexts = [{
        "id": "test1",
        "text": "BBCA ownership data...",
        "metadata": {"source": "ksei_json", "ticker": "BBCA", "date": "2026-03-31", "chunk_type": "ticker_summary"},
        "distance": 0.1,
    }]

    enrichment_text = "LIVE MARKET DATA (from Stockbit, real-time):\n\n--- BBCA ---\nForeign Flow: Net Buy Rp 45.0B"

    prompt = generate_enhanced_prompt(
        query="Who owns the most BBCA?",
        contexts=contexts,
        mode="balanced",
        enrichment_text=enrichment_text,
    )

    assert "LIVE MARKET DATA" in prompt
    assert "Net Buy" in prompt
    assert "CONTEXT INFORMATION" in prompt


def test_prompt_works_without_enrichment():
    """When enrichment_text is empty, prompt should work normally without LIVE DATA section."""
    contexts = [{
        "id": "test1",
        "text": "BBCA ownership data...",
        "metadata": {"source": "ksei_json", "ticker": "BBCA", "date": "2026-03-31", "chunk_type": "ticker_summary"},
        "distance": 0.1,
    }]

    prompt = generate_enhanced_prompt(
        query="Who owns the most BBCA?",
        contexts=contexts,
        mode="balanced",
        enrichment_text="",
    )

    assert "LIVE MARKET DATA" not in prompt
    assert "CONTEXT INFORMATION" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd d:/Kuliah/Project/vectoring && python -m pytest tests/test_rag_integration.py -v`
Expected: FAIL — `generate_enhanced_prompt` does not accept `enrichment_text` parameter

- [ ] **Step 3: Modify generate_enhanced_prompt in rag_enhanced.py**

In `src/rag_enhanced.py`, modify the `generate_enhanced_prompt` function signature (line 196) to accept `enrichment_text`, and insert the enrichment block into the prompt.

Change the function signature from:
```python
def generate_enhanced_prompt(
    query: str,
    contexts: List[Dict[str, Any]],
    mode: str = "balanced",
    include_quality_analysis: bool = True
) -> str:
```

To:
```python
def generate_enhanced_prompt(
    query: str,
    contexts: List[Dict[str, Any]],
    mode: str = "balanced",
    include_quality_analysis: bool = True,
    enrichment_text: str = "",
) -> str:
```

Then in the same function, change the prompt assembly (the f-string at line ~235) from:
```python
    prompt = f"""{system_prompt}

{mode_guidance}
{quality_section}
CONTEXT INFORMATION:
{context_block}
---

USER QUESTION: {query}

Provide your answer with appropriate confidence markers. If you cannot answer confidently, say so explicitly."""
```

To:
```python
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
```

- [ ] **Step 4: Modify ask_enhanced to call enricher**

In `src/rag_enhanced.py`, add an import at the top (after the existing imports around line 4):

```python
from stockbit_enricher import enrich_tickers, format_enrichment_for_prompt
```

Then in the `ask_enhanced` function (around line 340-345 where `generate_enhanced_prompt` is called), change:

```python
    # Generate enhanced prompt
    prompt = generate_enhanced_prompt(
        question, contexts, mode, include_quality_analysis
    )
```

To:

```python
    # Live enrichment from Stockbit
    tickers = extract_tickers(question)
    enrichment_data = enrich_tickers(tickers) if tickers else {}
    enrichment_text = format_enrichment_for_prompt(enrichment_data)

    # Generate enhanced prompt
    prompt = generate_enhanced_prompt(
        question, contexts, mode, include_quality_analysis,
        enrichment_text=enrichment_text,
    )
```

And in the return dict at the end of `ask_enhanced` (~line 392), add the enrichment data:

Change:
```python
    return {
        "question": question,
        "answer": response['text'],
        "sources": formatted_sources,
        "quality": quality,
        "success": True,
        "mode": mode,
        "error": None,
        "usage": response.get('usage', {}),
    }
```

To:
```python
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
```

Also add `"enrichment": {}` to all the early-return error dicts in `ask_enhanced` (the ones around lines 278-288, 295-300, 325-339).

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd d:/Kuliah/Project/vectoring && python -m pytest tests/test_rag_integration.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/rag_enhanced.py tests/test_rag_integration.py
git commit -m "feat: wire stockbit enrichment into RAG pipeline prompt assembly"
```

---

## Task 6: API — Add Enrichment to /ask Response and New /api/ticker Endpoint

**Files:**
- Modify: `src/api.py:50-67` (AskRequest/AskResponse models) and add new endpoint

- [ ] **Step 1: Modify AskResponse model in api.py**

In `src/api.py`, change the `AskResponse` model (line 59):

From:
```python
class AskResponse(BaseModel):
    question: str
    answer: Optional[str]
    sources: List[Dict[str, Any]]
    quality: Optional[Dict[str, Any]]
    mode: str
    success: bool
    error: Optional[str]
```

To:
```python
class AskResponse(BaseModel):
    question: str
    answer: Optional[str]
    sources: List[Dict[str, Any]]
    quality: Optional[Dict[str, Any]]
    mode: str
    success: bool
    error: Optional[str]
    enrichment: Optional[Dict[str, Any]] = None
```

- [ ] **Step 2: Pass enrichment through in the /ask endpoint**

In the `ask_endpoint` function (around line 184), change:

```python
    return AskResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result["sources"],
        quality=result.get("quality"),
        mode=result["mode"],
        success=result["success"],
        error=result.get("error")
    )
```

To:
```python
    return AskResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result["sources"],
        quality=result.get("quality"),
        mode=result["mode"],
        success=result["success"],
        error=result.get("error"),
        enrichment=result.get("enrichment"),
    )
```

- [ ] **Step 3: Add /api/ticker/{symbol} endpoint**

Add a new import at the top of `src/api.py`:
```python
from stockbit_enricher import enrich_tickers
```

Then add a new endpoint before the catch-all frontend route (before line 287):

```python
@app.get("/api/ticker/{symbol}")
def get_ticker_enrichment(symbol: str):
    """
    Get live Stockbit enrichment data for a single ticker.
    Returns foreign flow, price performance, and recent corporate actions.
    """
    symbol = symbol.upper()
    enrichment = enrich_tickers([symbol])
    data = enrichment.get(symbol, {})
    return {
        "ticker": symbol,
        "enrichment": data,
        "available": bool(data and any(v for v in data.values())),
    }
```

- [ ] **Step 4: Add Stockbit ingestion to /ingest endpoint**

In the `do_ingestion` function inside `ingest_endpoint` (around line 237), add Stockbit ingestion after the existing JSON/PDF ingestion:

Change:
```python
        def do_ingestion():
            ingestion_status["running"] = True
            try:
                result = {}
                
                if not pdf_only:
                    json_result = ingest_all_json_files(clear_existing=clear_existing)
                    result["json"] = json_result
                
                if not json_only:
                    pdf_result = ingest_all_pdfs()
                    result["pdf"] = pdf_result
                
                ingestion_status["last_result"] = result
                ingestion_status["running"] = False
                return result
            except Exception as e:
                ingestion_status["running"] = False
                ingestion_status["last_result"] = {"error": str(e)}
                raise
```

To:
```python
        def do_ingestion():
            ingestion_status["running"] = True
            try:
                result = {}
                
                if not pdf_only:
                    json_result = ingest_all_json_files(clear_existing=clear_existing)
                    result["json"] = json_result
                
                if not json_only:
                    pdf_result = ingest_all_pdfs()
                    result["pdf"] = pdf_result
                
                # Stockbit enrichment ingestion (runs after KSEI data)
                try:
                    from stockbit_ingest import ingest_all_stockbit
                    stockbit_result = ingest_all_stockbit()
                    result["stockbit"] = stockbit_result
                except Exception as e:
                    result["stockbit"] = {"error": str(e)}
                
                ingestion_status["last_result"] = result
                ingestion_status["running"] = False
                return result
            except Exception as e:
                ingestion_status["running"] = False
                ingestion_status["last_result"] = {"error": str(e)}
                raise
```

- [ ] **Step 5: Verify the API starts without errors**

Run: `cd d:/Kuliah/Project/vectoring/src && python -c "from api import app; print('API module loads OK')"`
Expected: "API module loads OK" (no import errors)

- [ ] **Step 6: Commit**

```bash
git add src/api.py
git commit -m "feat: add enrichment to /ask response and new /api/ticker endpoint"
```

---

## Task 7: Frontend Types — Add Enrichment Types

**Files:**
- Create: `frontend/src/types/enrichment.ts`
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Create enrichment types**

Create `frontend/src/types/enrichment.ts`:

```typescript
export interface ForeignFlow {
  ticker: string;
  foreign_buy: number;
  foreign_sell: number;
  foreign_net: number;
}

export interface PricePerformanceData {
  ticker: string;
  performance_1w: number | null;
  performance_1m: number | null;
  performance_3m: number | null;
  performance_6m: number | null;
  performance_ytd: number | null;
  performance_1y: number | null;
}

export interface CorpAction {
  ticker: string;
  action_type: string;
  description: string;
  ex_date: string | null;
  announcement_date: string | null;
}

export interface TickerEnrichment {
  foreign_flow: ForeignFlow | null;
  price_performance: PricePerformanceData | null;
  corp_actions: CorpAction[];
}

export type EnrichmentData = Record<string, TickerEnrichment>;
```

- [ ] **Step 2: Update AskResponse in api.ts**

In `frontend/src/types/api.ts`, add to the `AskResponse` interface:

Change:
```typescript
export interface AskResponse {
  question: string;
  answer: string | null;
  sources: any[];
  quality?: DataQuality;
  mode: string;
  success: boolean;
  error?: string;
}
```

To:
```typescript
import type { EnrichmentData } from './enrichment';

export interface AskResponse {
  question: string;
  answer: string | null;
  sources: any[];
  quality?: DataQuality;
  mode: string;
  success: boolean;
  error?: string;
  enrichment?: EnrichmentData;
}
```

- [ ] **Step 3: Export from index.ts**

In `frontend/src/types/index.ts`, add:

```typescript
export * from './enrichment';
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/enrichment.ts frontend/src/types/api.ts frontend/src/types/index.ts
git commit -m "feat(frontend): add enrichment TypeScript types"
```

---

## Task 8: Frontend — MarketContext Component

**Files:**
- Create: `frontend/src/components/chat/MarketContext.tsx`
- Modify: `frontend/src/components/chat/AIMessage.tsx`
- Modify: `frontend/src/types/chat.ts` (add enrichment to Message)

- [ ] **Step 1: Add enrichment to Message type**

In `frontend/src/types/chat.ts`, add the import and field:

Add at top:
```typescript
import type { EnrichmentData } from './enrichment';
```

Add to the `Message` interface after the `quality` field:
```typescript
  enrichment?: EnrichmentData;
```

- [ ] **Step 2: Create MarketContext component**

Create `frontend/src/components/chat/MarketContext.tsx`:

```tsx
import { TrendingUp, TrendingDown, DollarSign, Calendar, BarChart3 } from 'lucide-react';
import type { TickerEnrichment } from '@/types';

interface MarketContextProps {
  enrichment: Record<string, TickerEnrichment>;
}

function formatIDR(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1e12) return `Rp ${(value / 1e12).toFixed(1)}T`;
  if (abs >= 1e9) return `Rp ${(value / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `Rp ${(value / 1e6).toFixed(0)}M`;
  return `Rp ${value.toLocaleString()}`;
}

function PerfBadge({ label, value }: { label: string; value: number | null }) {
  if (value === null || value === undefined) return null;
  const isPositive = value > 0;
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs px-1.5 py-0.5 rounded
      ${isPositive ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
      {label}: {isPositive ? '+' : ''}{value}%
    </span>
  );
}

function TickerCard({ ticker, data }: { ticker: string; data: TickerEnrichment }) {
  const flow = data.foreign_flow;
  const perf = data.price_performance;
  const actions = data.corp_actions;

  const hasData = flow || perf || (actions && actions.length > 0);
  if (!hasData) return null;

  return (
    <div className="p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border)]">
      <div className="flex items-center gap-2 mb-2">
        <BarChart3 size={14} className="text-[var(--accent)]" />
        <span className="text-sm font-semibold text-[var(--text-primary)]">{ticker}</span>
        <span className="text-xs text-[var(--text-muted)]">Live Data</span>
      </div>

      {/* Foreign Flow */}
      {flow && (
        <div className="flex items-center gap-2 mb-2">
          {flow.foreign_net > 0 ? (
            <TrendingUp size={14} className="text-green-400" />
          ) : (
            <TrendingDown size={14} className="text-red-400" />
          )}
          <span className="text-sm text-[var(--text-secondary)]">
            Foreign {flow.foreign_net > 0 ? 'Net Buy' : 'Net Sell'}:{' '}
            <span className={flow.foreign_net > 0 ? 'text-green-400' : 'text-red-400'}>
              {formatIDR(Math.abs(flow.foreign_net))}
            </span>
          </span>
        </div>
      )}

      {/* Price Performance */}
      {perf && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          <PerfBadge label="1W" value={perf.performance_1w} />
          <PerfBadge label="1M" value={perf.performance_1m} />
          <PerfBadge label="3M" value={perf.performance_3m} />
          <PerfBadge label="YTD" value={perf.performance_ytd} />
          <PerfBadge label="1Y" value={perf.performance_1y} />
        </div>
      )}

      {/* Corporate Actions */}
      {actions && actions.length > 0 && (
        <div className="mt-2 pt-2 border-t border-[var(--border)]">
          {actions.map((action, i) => (
            <div key={i} className="flex items-start gap-1.5 text-xs text-[var(--text-muted)]">
              <Calendar size={12} className="mt-0.5 text-[var(--accent-gold)]" />
              <span>
                {action.description}
                {action.ex_date && (
                  <span className="text-[var(--text-muted)]"> (ex: {action.ex_date})</span>
                )}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function MarketContext({ enrichment }: MarketContextProps) {
  const tickers = Object.keys(enrichment);
  if (tickers.length === 0) return null;

  // Check if any ticker has actual data
  const hasAnyData = tickers.some((t) => {
    const d = enrichment[t];
    return d.foreign_flow || d.price_performance || (d.corp_actions && d.corp_actions.length > 0);
  });

  if (!hasAnyData) return null;

  return (
    <div className="mt-4 space-y-2">
      <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
        <DollarSign size={12} />
        <span>Market Context</span>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {tickers.map((ticker) => (
          <TickerCard key={ticker} ticker={ticker} data={enrichment[ticker]} />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Wire MarketContext into AIMessage**

In `frontend/src/components/chat/AIMessage.tsx`, add the import at the top:

```typescript
import { MarketContext } from './MarketContext';
```

Then in the JSX, after the confidence indicators section (after line ~84, before the Markdown Content section), add:

```tsx
          {/* Market Context Cards */}
          {message.enrichment && Object.keys(message.enrichment).length > 0 && (
            <MarketContext enrichment={message.enrichment} />
          )}
```

- [ ] **Step 4: Pass enrichment data through in ChatInput**

In `frontend/src/components/chat/ChatInput.tsx`, in the `handleSubmit` function, update the `aiMessage` construction (around line 45):

Change:
```typescript
      const aiMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: response.answer || 'Maaf, saya tidak dapat menjawab pertanyaan tersebut.',
        timestamp: new Date(),
        sources: response.sources,
        latency,
        quality: response.quality,
      };
```

To:
```typescript
      const aiMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: response.answer || 'Maaf, saya tidak dapat menjawab pertanyaan tersebut.',
        timestamp: new Date(),
        sources: response.sources,
        latency,
        quality: response.quality,
        enrichment: response.enrichment,
      };
```

- [ ] **Step 5: Implement the getMarketData placeholder in api.ts**

In `frontend/src/lib/api.ts`, replace the placeholder `getMarketData` function:

Change:
```typescript
export async function getMarketData(
  ticker: string
): Promise<{ ticker: string; price: number; change: number } | null> {
  // Placeholder - will be implemented with Stockbit API
  console.log('Market data fetch requested for:', ticker);
  return null;
}
```

To:
```typescript
export async function getMarketData(
  ticker: string
): Promise<{ ticker: string; enrichment: any; available: boolean } | null> {
  try {
    return await fetchApi(`/api/ticker/${ticker.toUpperCase()}`);
  } catch {
    return null;
  }
}
```

And replace `getBatchMarketData`:

Change:
```typescript
export async function getBatchMarketData(
  tickers: string[]
): Promise<Record<string, { price: number; change: number }>> {
  // Placeholder - will be implemented with Stockbit API
  console.log('Batch market data fetch requested for:', tickers);
  return {};
}
```

To:
```typescript
export async function getBatchMarketData(
  tickers: string[]
): Promise<Record<string, any>> {
  const results: Record<string, any> = {};
  await Promise.all(
    tickers.map(async (ticker) => {
      const data = await getMarketData(ticker);
      if (data?.available) {
        results[ticker] = data.enrichment;
      }
    })
  );
  return results;
}
```

- [ ] **Step 6: Verify frontend compiles**

Run: `cd d:/Kuliah/Project/vectoring/frontend && npx tsc --noEmit`
Expected: No errors (or only pre-existing ones)

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/chat/MarketContext.tsx frontend/src/components/chat/AIMessage.tsx frontend/src/components/chat/ChatInput.tsx frontend/src/types/chat.ts frontend/src/lib/api.ts
git commit -m "feat(frontend): add MarketContext card showing live stockbit data in AI messages"
```

---

## Task 9: Add pydantic-settings to requirements.txt

**Files:**
- Modify: `requirements.txt`

The `stockbit/` library imports `pydantic_settings` which may not be installed.

- [ ] **Step 1: Add pydantic-settings**

In `requirements.txt`, add after the `pydantic>=2.0.0` line:

```
pydantic-settings>=2.0.0
```

- [ ] **Step 2: Verify install**

Run: `cd d:/Kuliah/Project/vectoring && pip install pydantic-settings`
Expected: Installs successfully

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add pydantic-settings dependency for stockbit lib"
```

---

## Task 10: Run Full Test Suite and Verify

**Files:**
- No new files

- [ ] **Step 1: Run all backend tests**

Run: `cd d:/Kuliah/Project/vectoring && python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Verify API starts**

Run: `cd d:/Kuliah/Project/vectoring/src && python -c "from api import app; print('OK')"`
Expected: "OK"

- [ ] **Step 3: Verify frontend compiles**

Run: `cd d:/Kuliah/Project/vectoring/frontend && npx tsc --noEmit`
Expected: No new errors

- [ ] **Step 4: Final commit with test run proof**

```bash
git add -A
git commit -m "test: verify full stockbit integration passes"
```

---

## Summary

| Task | What It Does | Files |
|---|---|---|
| 1 | Config: Add STOCKBIT_TOKEN | `src/config.py`, `.env.example` |
| 2 | Test fixtures for all mocked Stockbit responses | `tests/conftest.py` |
| 3 | Periodic ingestion: profiles, ratios, consensus, holders -> ChromaDB | `src/stockbit_ingest.py` |
| 4 | Live enrichment: foreign flow, prices, corp actions at query time | `src/stockbit_enricher.py` |
| 5 | Wire enricher into RAG pipeline and prompt assembly | `src/rag_enhanced.py` |
| 6 | API: enrichment in /ask response + new /api/ticker endpoint | `src/api.py` |
| 7 | Frontend types for enrichment data | `frontend/src/types/` |
| 8 | MarketContext card in AI messages | `frontend/src/components/chat/` |
| 9 | Add pydantic-settings dependency | `requirements.txt` |
| 10 | Verify everything works together | All |
