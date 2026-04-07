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
