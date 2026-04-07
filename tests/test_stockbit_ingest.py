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
