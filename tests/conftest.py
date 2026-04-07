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
