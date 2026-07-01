"""
Embed market data from DuckDB into ChromaDB for RAG retrieval.

Design: 7 chunk types, one chunk per symbol each.
Text is bilingual (Indonesian + English) so both language queries resolve correctly.
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from typing import List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

CHUNK_TYPES = [
    "market_price",
    "market_company",
    "market_ratios",
    "market_financials",
    "market_performance",
    "market_analyst",
    "market_actions",
]

_PERIOD_LABELS = {
    "1d":  ("Harian / 1 Day",         "1D"),
    "1w":  ("Mingguan / 1 Week",       "1W"),
    "1m":  ("Bulanan / 1 Month",       "1M"),
    "3m":  ("3 Bulan / 3 Months",      "3M"),
    "6m":  ("6 Bulan / 6 Months",      "6M"),
    "ytd": ("YTD / Year to Date",      "YTD"),
    "1y":  ("1 Tahun / 1 Year",        "1Y"),
    "3y":  ("3 Tahun / 3 Years",       "3Y"),
    "5y":  ("5 Tahun / 5 Years",       "5Y"),
    "10y": ("10 Tahun / 10 Years",     "10Y"),
}


# ── helpers ──────────────────────────────────────────────────────────────────

def _f(v, decimals=2, suffix=""):
    """Format number or return N/A."""
    if v is None:
        return "N/A"
    return f"{v:.{decimals}f}{suffix}"


def _idr(v):
    """Format IDR value in trillions/billions/millions for readability."""
    if v is None:
        return "N/A"
    abs_v = abs(v)
    sign  = "-" if v < 0 else ""
    if abs_v >= 1e12:
        return f"{sign}Rp {abs_v/1e12:.2f}T"
    if abs_v >= 1e9:
        return f"{sign}Rp {abs_v/1e9:.1f}M"   # M = miliar (billion)
    if abs_v >= 1e6:
        return f"{sign}Rp {abs_v/1e6:.0f}jt"
    return f"{sign}Rp {v:,.0f}"


def _placeholders(symbols):
    return ",".join(["?"] * len(symbols))


def _upsert(texts: List[str], ids: List[str], metas: List[dict], batch=100):
    from embedder import upsert_with_ids
    return upsert_with_ids(texts, ids, metas, batch_size=batch)


def _name_map(conn, symbols=None) -> dict:
    """Return {symbol: name} lookup from stocks table."""
    if symbols:
        rows = conn.execute(
            f"SELECT symbol, name FROM stocks WHERE symbol IN ({_placeholders(symbols)})",
            symbols,
        ).fetchall()
    else:
        rows = conn.execute("SELECT symbol, name FROM stocks").fetchall()
    return {r[0]: r[1] or r[0] for r in rows}


def _sym_filter(base_q: str, symbols, params_before=None) -> tuple[str, list]:
    """Append WHERE symbol IN (...) to query and return (q, params)."""
    p = list(params_before or [])
    if symbols:
        base_q += f" AND symbol IN ({_placeholders(symbols)})"
        p += list(symbols)
    return base_q, p


# ── 1. market_price ───────────────────────────────────────────────────────────

def embed_price(conn, symbols: Optional[List[str]] = None) -> int:
    """Latest OHLCV snapshot — current price, volume, foreign flow, 30d range."""
    q = """
        SELECT o.symbol, o.date, o.close, o.volume, o.net_foreign,
               r30.low30, r30.high30, r30.avg_vol
        FROM (
            SELECT symbol, MAX(date) AS latest FROM ohlcv_daily
            GROUP BY symbol
        ) latest_date
        JOIN ohlcv_daily o ON o.symbol = latest_date.symbol AND o.date = latest_date.latest
        LEFT JOIN (
            SELECT symbol,
                   MIN(low)  AS low30,
                   MAX(high) AS high30,
                   AVG(volume) AS avg_vol
            FROM ohlcv_daily
            GROUP BY symbol
        ) r30 ON r30.symbol = o.symbol
    """
    params = []
    if symbols:
        q += f" WHERE o.symbol IN ({_placeholders(symbols)})"
        params = symbols

    rows = conn.execute(q, params).fetchall()
    names = _name_map(conn, symbols)
    texts, ids, metas = [], [], []

    for symbol, dt, close, volume, net_foreign, low30, high30, avg_vol in rows:
        name    = names.get(symbol, symbol)
        net_f   = net_foreign or 0
        net_lbl = f"+Rp {net_f/1e9:.1f}M" if net_f >= 0 else f"-Rp {abs(net_f)/1e9:.1f}M"

        text = (
            f"Harga saham / Stock price {symbol} - {name} per {dt}:\n"
            f"Harga penutupan / Close price: Rp {close:,.0f}\n"
            f"Volume perdagangan / Trading volume: {volume:,} lot\n"
            f"Net aliran asing / Net foreign flow: {net_lbl} miliar\n"
            f"Rentang harga (semua data) / Price range: Rp {low30:,.0f} - Rp {high30:,.0f}\n"
            f"Rata-rata volume / Avg volume: {avg_vol:,.0f}"
        )
        texts.append(text)
        ids.append(f"market_price_{symbol}")
        metas.append({
            "chunk_type": "market_price",
            "ticker": symbol,
            "date": str(dt),
            "close": str(close or ""),
        })

    return _upsert(texts, ids, metas) if texts else 0


# ── 2. market_company ─────────────────────────────────────────────────────────

def embed_companies(conn, symbols: Optional[List[str]] = None) -> int:
    q = "SELECT symbol, name, sector, industry, description FROM stocks WHERE 1=1"
    params = []
    if symbols:
        q += f" AND symbol IN ({_placeholders(symbols)})"
        params = symbols

    rows = conn.execute(q, params).fetchall()
    texts, ids, metas = [], [], []

    for symbol, name, sector, industry, description in rows:
        display_name = name or symbol
        text = (
            f"Perusahaan / Company: {display_name} ({symbol})\n"
            f"Sektor / Sector: {sector or 'N/A'}\n"
            f"Industri / Industry: {industry or 'N/A'}\n"
        )
        if description and description.strip():
            text += f"Deskripsi / Description: {description.strip()}"
        texts.append(text.strip())
        ids.append(f"market_company_{symbol}")
        metas.append({
            "chunk_type": "market_company",
            "ticker": symbol,
            "name": display_name,
            "sector": sector or "",
        })

    return _upsert(texts, ids, metas) if texts else 0


# ── 3. market_ratios ──────────────────────────────────────────────────────────

def embed_ratios(conn, symbols: Optional[List[str]] = None) -> int:
    q = """
        SELECT fr.symbol, fr.date,
               fr.pe_ttm, fr.pe_forward, fr.pe_annualised,
               fr.pb, fr.ps_ttm, fr.ev_ebitda,
               fr.roe, fr.roa, fr.roic,
               fr.gross_margin, fr.operating_margin,
               fr.debt_equity, fr.current_ratio, fr.interest_coverage,
               fr.dividend_yield, fr.payout_ratio, fr.earnings_yield
        FROM fundamentals_ratio fr
        JOIN (SELECT symbol, MAX(date) AS d FROM fundamentals_ratio GROUP BY symbol) latest
          ON fr.symbol = latest.symbol AND fr.date = latest.d
        WHERE 1=1
    """
    params = []
    if symbols:
        q += f" AND fr.symbol IN ({_placeholders(symbols)})"
        params = symbols

    rows = conn.execute(q, params).fetchall()
    names = _name_map(conn, symbols)
    texts, ids, metas = [], [], []

    for r in rows:
        (symbol, dt, pe_ttm, pe_fwd, pe_ann, pb, ps, ev_eb,
         roe, roa, roic, gm, om, de, cr, ic, dy, pr, ey) = r
        name = names.get(symbol, symbol)

        text = (
            f"Rasio keuangan / Financial ratios {symbol} - {name} per {dt}:\n"
            f"\n"
            f"Valuasi / Valuation:\n"
            f"  PE ratio (TTM / Price-to-Earnings): {_f(pe_ttm)}x\n"
            f"  PE Annualized (PE Tahunan): {_f(pe_ann)}x\n"
            f"  PE Forward (Estimasi): {_f(pe_fwd)}x\n"
            f"  PB ratio (Price-to-Book / Harga terhadap Nilai Buku): {_f(pb)}x\n"
            f"  PS ratio (Price-to-Sales): {_f(ps)}x\n"
            f"  EV/EBITDA: {_f(ev_eb)}x\n"
            f"\n"
            f"Profitabilitas / Profitability:\n"
            f"  ROE (Return on Equity / Imbal Ekuitas): {_f(roe)}%\n"
            f"  ROA (Return on Assets / Imbal Aset): {_f(roa)}%\n"
            f"  ROIC (Return on Invested Capital): {_f(roic)}%\n"
            f"  Gross Margin (Margin Laba Kotor): {_f(gm)}%\n"
            f"  Operating Margin (Margin Operasi): {_f(om)}%\n"
            f"\n"
            f"Kesehatan keuangan / Financial health:\n"
            f"  Debt/Equity (Utang terhadap Ekuitas): {_f(de)}\n"
            f"  Current Ratio (Rasio Lancar): {_f(cr)}\n"
            f"  Interest Coverage: {_f(ic)}\n"
            f"\n"
            f"Imbal hasil / Yield:\n"
            f"  Dividend Yield (Imbal Dividen): {_f(dy)}%\n"
            f"  Payout Ratio (Rasio Pembayaran Dividen): {_f(pr)}%\n"
            f"  Earnings Yield: {_f(ey)}%"
        )
        texts.append(text)
        ids.append(f"market_ratios_{symbol}")
        metas.append({
            "chunk_type": "market_ratios",
            "ticker": symbol,
            "date": str(dt) if dt else "",
            "roe": str(roe or ""),
            "pe_ttm": str(pe_ttm or ""),
            "dividend_yield": str(dy or ""),
        })

    return _upsert(texts, ids, metas) if texts else 0


# ── 4. market_financials ──────────────────────────────────────────────────────

# Key income statement line items to include
_INCOME_ITEMS = [
    "Total Revenue",
    "Net Income",
    "Gross Profit",
    "Operating Income",
    "Income Before Tax",
    "EBITDA (Quarter)",
    "EPS (Quarter)",
]

def embed_financials(conn, symbols: Optional[List[str]] = None) -> int:
    """Income statement highlights, last 6 quarters, IDR formatted in trillions."""
    q = """
        SELECT symbol, period_end, line_item, value
        FROM financials_quarterly
        WHERE statement_type = 'income_statement'
    """
    params = []
    if symbols:
        q += f" AND symbol IN ({_placeholders(symbols)})"
        params = symbols
    q += " ORDER BY symbol, period_end DESC"

    rows = conn.execute(q, params).fetchall()
    names = _name_map(conn, symbols)

    # Group: {symbol: {period_end: {line_item: value}}}
    by_sym: dict = defaultdict(lambda: defaultdict(dict))
    for symbol, period_end, line_item, value in rows:
        by_sym[symbol][str(period_end)][line_item] = value

    texts, ids, metas = [], [], []

    for symbol, periods in by_sym.items():
        name           = names.get(symbol, symbol)
        sorted_periods = sorted(periods.keys(), reverse=True)[:6]

        lines = [
            f"Laporan keuangan kuartalan / Quarterly income statement {symbol} - {name}:",
            f"(dalam miliar / triliun IDR)",
            "",
        ]
        for period in sorted_periods:
            items = periods[period]
            rev  = _idr(items.get("Total Revenue"))
            ni   = _idr(items.get("Net Income"))
            gp   = _idr(items.get("Gross Profit"))
            ebit = _idr(items.get("EBITDA (Quarter)"))
            eps  = items.get("EPS (Quarter)")
            eps_str = f"Rp {eps:.0f}/saham" if eps is not None else "N/A"
            lines.append(
                f"{period}: Pendapatan/Revenue={rev} | "
                f"Laba Bersih/Net Income={ni} | "
                f"Laba Kotor/Gross Profit={gp} | "
                f"EBITDA={ebit} | EPS={eps_str}"
            )

        latest_p = sorted_periods[0] if sorted_periods else ""
        oldest_p = sorted_periods[-1] if sorted_periods else ""

        texts.append("\n".join(lines))
        ids.append(f"market_financials_{symbol}")
        metas.append({
            "chunk_type": "market_financials",
            "ticker": symbol,
            "latest_period": latest_p,
            "oldest_period": oldest_p,
        })

    return _upsert(texts, ids, metas) if texts else 0


# ── 5. market_performance ─────────────────────────────────────────────────────

def embed_performance(conn, symbols: Optional[List[str]] = None) -> int:
    q = """
        SELECT symbol, as_of_date, period, change_pct, high, low
        FROM price_performance
    """
    params = []
    if symbols:
        q += f" WHERE symbol IN ({_placeholders(symbols)})"
        params = symbols
    q += " ORDER BY symbol, as_of_date DESC"

    rows = conn.execute(q, params).fetchall()
    names = _name_map(conn, symbols)

    # Latest snapshot per symbol per period
    by_sym: dict = defaultdict(dict)
    for symbol, dt, period, chg, high, low in rows:
        if period not in by_sym[symbol]:
            by_sym[symbol][period] = (chg, high, low, dt)

    texts, ids, metas = [], [], []

    for symbol, periods in by_sym.items():
        name = names.get(symbol, symbol)

        def fmt(p):
            v = periods.get(p)
            if not v or v[0] is None:
                return "N/A"
            sign = "+" if v[0] >= 0 else ""
            return f"{sign}{v[0]:.2f}%"

        lines = [
            f"Performa harga saham / Stock price performance {symbol} - {name}:",
        ]
        for period_key, (label_id, label_en) in _PERIOD_LABELS.items():
            v = periods.get(period_key)
            if v and v[0] is not None:
                sign = "+" if v[0] >= 0 else ""
                hi   = f"Rp {v[1]:,.0f}" if v[1] else "-"
                lo   = f"Rp {v[2]:,.0f}" if v[2] else "-"
                lines.append(
                    f"  {label_id}: {sign}{v[0]:.2f}%  "
                    f"(high {hi}, low {lo})"
                )

        texts.append("\n".join(lines))
        ids.append(f"market_perf_{symbol}")
        metas.append({
            "chunk_type": "market_performance",
            "ticker": symbol,
            "ytd": fmt("ytd"),
            "1y": fmt("1y"),
        })

    return _upsert(texts, ids, metas) if texts else 0


# ── 6. market_analyst ─────────────────────────────────────────────────────────

def embed_analyst(conn, symbols: Optional[List[str]] = None) -> int:
    q = """
        SELECT ac.symbol, ac.date, ac.consensus_rating,
               ac.target_median, ac.target_high, ac.target_low,
               ac.estimate_revision_30d_up, ac.estimate_revision_30d_down
        FROM analyst_consensus ac
        JOIN (SELECT symbol, MAX(date) AS d FROM analyst_consensus GROUP BY symbol) latest
          ON ac.symbol = latest.symbol AND ac.date = latest.d
        WHERE 1=1
    """
    params = []
    if symbols:
        q += f" AND ac.symbol IN ({_placeholders(symbols)})"
        params = symbols

    rows = conn.execute(q, params).fetchall()
    names = _name_map(conn, symbols)

    # Count ratings by symbol: {symbol: {rating: count}}
    rq = "SELECT symbol, rating, COUNT(*) FROM analyst_ratings WHERE rating IS NOT NULL AND rating != '' GROUP BY symbol, rating"
    rparams = []
    if symbols:
        rq = f"SELECT symbol, rating, COUNT(*) FROM analyst_ratings WHERE rating IS NOT NULL AND rating != '' AND symbol IN ({_placeholders(symbols)}) GROUP BY symbol, rating"
        rparams = symbols
    rating_map: dict = defaultdict(dict)
    for sym, rating, cnt in conn.execute(rq, rparams).fetchall():
        rating_map[sym][rating] = cnt

    texts, ids, metas = [], [], []

    for symbol, dt, cons, t_med, t_hi, t_lo, rev_up, rev_dn in rows:
        name = names.get(symbol, symbol)
        rc   = rating_map.get(symbol, {})

        # Aggregate buy/hold/sell
        buys  = sum(v for k, v in rc.items() if "buy" in k.lower())
        holds = sum(v for k, v in rc.items() if "hold" in k.lower() or "neutral" in k.lower())
        sells = sum(v for k, v in rc.items() if "sell" in k.lower())
        total = buys + holds + sells

        # Determine consensus label if not stored
        cons_label = cons
        if not cons_label and total > 0:
            if buys >= holds and buys >= sells:
                cons_label = "Buy"
            elif sells >= holds:
                cons_label = "Sell"
            else:
                cons_label = "Hold"

        target_str = "N/A"
        if t_med:
            target_str = f"Rp {t_med:,.0f}"
            if t_hi:
                target_str += f"  (high Rp {t_hi:,.0f}"
            if t_lo:
                target_str += f", low Rp {t_lo:,.0f})"
            elif t_hi:
                target_str += ")"

        text = (
            f"Rekomendasi analis / Analyst recommendations {symbol} - {name} per {dt}:\n"
            f"Konsensus / Consensus rating: {cons_label or 'N/A'}\n"
            f"Target harga / Price target: {target_str}\n"
            f"Jumlah analis / Analyst count: {total} total — "
            f"Buy={buys}, Hold={holds}, Sell={sells}\n"
        )
        if rev_up is not None or rev_dn is not None:
            text += (
                f"Revisi estimasi 30 hari / 30-day estimate revisions: "
                f"up={rev_up or 0}, down={rev_dn or 0}"
            )

        texts.append(text.strip())
        ids.append(f"market_analyst_{symbol}")
        metas.append({
            "chunk_type": "market_analyst",
            "ticker": symbol,
            "consensus": cons_label or "",
            "target_price": str(t_med or ""),
        })

    return _upsert(texts, ids, metas) if texts else 0


# ── 7. market_actions ─────────────────────────────────────────────────────────

def embed_actions(conn, symbols: Optional[List[str]] = None) -> int:
    q = """
        SELECT symbol, action_type, announce_date, ex_date, pay_date, cash_amount, notes
        FROM corporate_actions
    """
    params = []
    if symbols:
        q += f" WHERE symbol IN ({_placeholders(symbols)})"
        params = symbols
    q += " ORDER BY symbol, announce_date DESC NULLS LAST"

    rows = conn.execute(q, params).fetchall()
    names = _name_map(conn, symbols)

    by_sym: dict = defaultdict(list)
    for symbol, atype, ann_dt, ex_dt, pay_dt, cash, notes in rows:
        by_sym[symbol].append((atype, ann_dt, ex_dt, pay_dt, cash, notes))

    texts, ids, metas = [], [], []

    for symbol, actions in by_sym.items():
        name = names.get(symbol, symbol)

        # Separate by type
        dividends = [(a, e, p, c, n) for (t, a, e, p, c, n) in actions if t == "dividend"]
        others    = [(t, a, e, p, c, n) for (t, a, e, p, c, n) in actions if t != "dividend"]

        lines = [
            f"Aksi korporasi / Corporate actions {symbol} - {name}:",
            "",
        ]

        # Dividends (most important for RAG)
        if dividends:
            lines.append(f"Dividen / Dividends ({len(dividends)} total):")
            for ann_dt, ex_dt, pay_dt, cash, notes in dividends[:6]:
                parts = []
                if ann_dt:
                    parts.append(f"announced {ann_dt}")
                if ex_dt:
                    parts.append(f"ex-date {ex_dt}")
                if pay_dt:
                    parts.append(f"pay-date {pay_dt}")
                cash_str = f"Rp {cash:,.0f}/saham" if cash else "N/A"
                lines.append(f"  Dividen {cash_str}  [{', '.join(parts)}]")

        # Other events (RUPS, rights issue, splits)
        if others:
            lines.append(f"\nAksi lainnya / Other events:")
            type_counts: dict = defaultdict(int)
            for t, *_ in others:
                type_counts[t] += 1
            for t, cnt in sorted(type_counts.items()):
                lines.append(f"  {t}: {cnt} event(s)")

        texts.append("\n".join(lines))
        ids.append(f"market_actions_{symbol}")
        metas.append({
            "chunk_type": "market_actions",
            "ticker": symbol,
            "dividend_count": str(len(dividends)),
        })

    return _upsert(texts, ids, metas) if texts else 0


# ── entry point ───────────────────────────────────────────────────────────────

def embed_all(db_path: str, symbols: Optional[List[str]] = None) -> dict:
    import duckdb
    import embedder as _embedder  # pre-load model before any lazy imports inside _upsert
    _ = _embedder.EMBEDDING_MODEL  # ensure model is initialized
    conn = duckdb.connect(db_path, read_only=True)
    results = {}
    for fn, label in [
        (embed_price,       "price"),
        (embed_companies,   "company"),
        (embed_ratios,      "ratios"),
        (embed_financials,  "financials"),
        (embed_performance, "performance"),
        (embed_analyst,     "analyst"),
        (embed_actions,     "actions"),
    ]:
        n = fn(conn, symbols)
        results[label] = n
        print(f"  {label}: {n} chunks")
    conn.close()
    return results
