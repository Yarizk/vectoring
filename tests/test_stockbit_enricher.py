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
    """Should return enrichment dict with None values if API fails, not raise."""
    client = MagicMock()
    client.financials.get_foreign_domestic_flow.side_effect = Exception("API down")
    client.quotes.get_price_performance.side_effect = Exception("API down")
    client.corporate_actions.get_by_symbol.side_effect = Exception("API down")
    mock_get_client.return_value = client

    result = enrich_tickers(["BBCA"])
    # Should not raise — returns dict with None values
    assert "BBCA" in result
    assert result["BBCA"]["foreign_flow"] is None
