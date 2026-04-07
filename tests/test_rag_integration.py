"""Tests for RAG pipeline integration with Stockbit enrichment."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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
