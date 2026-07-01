"""
Stockbit API scrapers for vectoring market data.

Scrapes OHLCV, ratios, financials, analyst, price performance, and
corporate actions for a list of symbols and stores to DuckDB.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import date, timedelta
from typing import List, Optional

# Add sbitv2 root so `from stockbit import StockbitClient` resolves
_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
_PROJECT = os.path.dirname(_SRC)
_SBITV2 = os.path.join(os.path.dirname(_PROJECT), "sbitv2")
if _SBITV2 not in sys.path:
    sys.path.insert(0, _SBITV2)

# Ratio name → column mapping (from Stockbit /keystats/ratio/v1/{symbol})
_RATIO_MAP = {
    "Current PE Ratio (TTM)":           "pe_ttm",
    "Forward PE Ratio":                 "pe_forward",
    "Current PE Ratio (Annualised)":    "pe_annualised",
    "Current Price to Book Value":      "pb",
    "Current Price to Sales (TTM)":     "ps_ttm",
    "EV to EBITDA (TTM)":               "ev_ebitda",
    "Return on Equity (TTM)":           "roe",
    "Return on Assets (TTM)":           "roa",
    "Return On Invested Capital (TTM)": "roic",
    "Gross Profit Margin (Quarter)":    "gross_margin",
    "Operating Profit Margin (Quarter)":"operating_margin",
    "Debt to Equity Ratio (Quarter)":   "debt_equity",
    "Current Ratio (Quarter)":          "current_ratio",
    "Interest Coverage (TTM)":          "interest_coverage",
    "Dividend Yield":                   "dividend_yield",
    "Payout Ratio":                     "payout_ratio",
    "Earnings Yield (TTM)":             "earnings_yield",
}
_RATIO_COLS = list(set(_RATIO_MAP.values()))

_INCOME_LINE_ITEMS = {
    "Revenue": "Revenue",
    "Net Income": "Net Income",
    "Gross Profit": "Gross Profit",
    "Operating Income": "Operating Income",
    "EBITDA": "EBITDA",
}


def _val(obj, key):
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "").replace("%", "")
    if not s or s == "-":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _date(v) -> Optional[date]:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Per-type scrapers
# ---------------------------------------------------------------------------

def scrape_ohlcv(client, symbol: str, conn, since: str, until: str) -> int:
    try:
        resp = client.quotes.get_chartbit_daily(symbol, from_date=since, to_date=until)
    except Exception as e:
        print(f"    ohlcv: {e}")
        return 0

    candles = getattr(resp, "chartbit", None) or []
    rows = []
    for c in candles:
        d = _date(_val(c, "date"))
        if d is None:
            continue
        fbuy  = _num(_val(c, "foreignbuy"))
        fsell = _num(_val(c, "foreignsell"))
        rows.append((
            symbol,
            d,
            _num(_val(c, "open")),
            _num(_val(c, "high")),
            _num(_val(c, "low")),
            _num(_val(c, "close")),
            _val(c, "volume"),
            _num(_val(c, "value")),
            _val(c, "frequency"),
            fbuy,
            fsell,
            (fbuy - fsell) if fbuy is not None and fsell is not None else None,
        ))
    if not rows:
        return 0
    conn.executemany("""
        INSERT INTO ohlcv_daily
            (symbol, date, open, high, low, close, volume, value,
             frequency, foreign_buy, foreign_sell, net_foreign)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT (symbol, date) DO UPDATE SET
            open=excluded.open, high=excluded.high, low=excluded.low,
            close=excluded.close, volume=excluded.volume, value=excluded.value,
            frequency=excluded.frequency,
            foreign_buy=excluded.foreign_buy, foreign_sell=excluded.foreign_sell,
            net_foreign=excluded.net_foreign
    """, rows)
    return len(rows)


def scrape_ratios(client, symbol: str, conn, as_of: date) -> bool:
    try:
        resp = client.financials.get_key_ratios(symbol)
    except Exception as e:
        print(f"    ratios: {e}")
        return False

    row = {c: None for c in _RATIO_COLS}
    groups = _val(resp, "closure_fin_items_results") or []
    for group in groups:
        for item in (_val(group, "fin_name_results") or []):
            fitem = _val(item, "fitem") or {}
            name  = _val(fitem, "name") or ""
            col   = _RATIO_MAP.get(name)
            if col and row[col] is None:
                row[col] = _num(_val(fitem, "value"))

    cols = ["symbol", "date"] + _RATIO_COLS
    ph   = ",".join(["?"] * len(cols))
    upd  = ",".join(f"{c}=excluded.{c}" for c in _RATIO_COLS)
    vals = [symbol, as_of] + [row[c] for c in _RATIO_COLS]
    conn.execute(f"""
        INSERT INTO fundamentals_ratio ({','.join(cols)}) VALUES ({ph})
        ON CONFLICT (symbol, date) DO UPDATE SET {upd}
    """, vals)
    return True


_REPORT_TYPE_NAMES = {1: "income_statement", 2: "balance_sheet", 3: "cash_flow"}

def scrape_financials(client, symbol: str, conn) -> int:
    """Scrape quarterly financials by parsing HTML from /findata-view/company/financial."""
    import sys as _sys
    _SBITV2 = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "sbitv2")
    if _SBITV2 not in _sys.path:
        _sys.path.insert(0, _SBITV2)
    try:
        from stockbit.utils.findata_html import parse_financial_html
    except ImportError as e:
        print(f"    financials: cannot import parser: {e}")
        return 0

    rows = []
    for rt_code, st_name in _REPORT_TYPE_NAMES.items():
        try:
            resp = client.financials.get_financials(
                symbol, data_type=1, report_type=rt_code, statement_type=1
            )
        except Exception as e:
            print(f"    financials({st_name}): {e}")
            continue
        if not isinstance(resp, dict):
            continue
        html     = resp.get("html_report") or ""
        currency = resp.get("default_currency") or "IDR"
        for parsed in parse_financial_html(html):
            rows.append((
                symbol,
                parsed["period_end"],
                st_name,
                parsed["line_item"],
                parsed["value"],
                currency,
            ))

    if not rows:
        return 0

    conn.execute("DELETE FROM financials_quarterly WHERE symbol = ?", [symbol])
    conn.executemany(
        """INSERT INTO financials_quarterly
               (symbol, period_end, statement_type, line_item, value, unit)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT (symbol, period_end, statement_type, line_item)
           DO UPDATE SET value=excluded.value, unit=excluded.unit""",
        rows,
    )
    return len(rows)


def _model_to_dict(obj) -> dict:
    """Convert Pydantic model or dict to plain dict."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return vars(obj)


def scrape_analyst(client, symbol: str, conn, as_of: date) -> bool:
    # get_consensus actually returns a list of individual ratings (same as get_ratings)
    # We aggregate them ourselves to build the consensus row.
    try:
        ratings_raw = client.analyst.get_consensus(symbol)
        if not isinstance(ratings_raw, list):
            ratings_raw = [ratings_raw] if ratings_raw else []

        conn.execute("DELETE FROM analyst_ratings WHERE symbol = ?", [symbol])
        rows = []
        buy_count = hold_count = sell_count = 0
        targets = []

        for r in ratings_raw:
            if r is None:
                continue
            rv = _model_to_dict(r) if not isinstance(r, dict) else r
            rating  = rv.get("rating") or ""
            analyst = rv.get("analyst") or ""
            pt      = _num(rv.get("price_target"))
            dt      = _date(rv.get("date")) or as_of
            rows.append((symbol, dt, analyst or "consensus", rating, pt, analyst))
            if pt:
                targets.append(pt)
            rl = rating.lower()
            if "buy" in rl:
                buy_count += 1
            elif "hold" in rl or "neutral" in rl:
                hold_count += 1
            elif "sell" in rl:
                sell_count += 1

        if rows:
            conn.executemany(
                "INSERT INTO analyst_ratings VALUES (?,?,?,?,?,?)", rows
            )

        # Build aggregate consensus
        total = buy_count + hold_count + sell_count
        if total > 0:
            if buy_count >= hold_count and buy_count >= sell_count:
                consensus_rating = "Buy"
            elif sell_count >= hold_count:
                consensus_rating = "Sell"
            else:
                consensus_rating = "Hold"
        else:
            consensus_rating = None

        t_med  = sorted(targets)[len(targets) // 2] if targets else None
        t_high = max(targets) if targets else None
        t_low  = min(targets) if targets else None

        conn.execute("""
            INSERT INTO analyst_consensus
                (symbol, date, consensus_rating, target_median,
                 target_high, target_low,
                 estimate_revision_30d_up, estimate_revision_30d_down)
            VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT (symbol, date) DO UPDATE SET
                consensus_rating=excluded.consensus_rating,
                target_median=excluded.target_median,
                target_high=excluded.target_high,
                target_low=excluded.target_low,
                estimate_revision_30d_up=excluded.estimate_revision_30d_up,
                estimate_revision_30d_down=excluded.estimate_revision_30d_down
        """, [symbol, as_of, consensus_rating, t_med, t_high, t_low, buy_count, sell_count])

    except Exception as e:
        print(f"    analyst: {e}")

    return True


def scrape_price_perf(client, symbol: str, conn, as_of: date) -> bool:
    try:
        perf = client.quotes.get_price_performance(symbol)
        if not perf:
            return False

        conn.execute(
            "DELETE FROM price_performance WHERE symbol = ?", [symbol]
        )
        # performance_1w etc. are None; actual data lives in perf.prices list
        # Each entry: {timeframe: '1W'|'1M'|'3M'|'6M'|'YTD'|'1Y', percentage: {raw: -4.47}, high: {raw:...}, low: {raw:...}}
        _TF_MAP = {"1D": "1d", "1W": "1w", "1M": "1m", "3M": "3m",
                   "6M": "6m", "YTD": "ytd", "1Y": "1y", "3Y": "3y", "5Y": "5y", "10Y": "10y"}
        prices = getattr(perf, "prices", None) or []
        rows = []
        for entry in prices:
            ev    = entry if isinstance(entry, dict) else _model_to_dict(entry)
            tf    = ev.get("timeframe", "")
            period = _TF_MAP.get(tf)
            if not period:
                continue
            pct_obj = ev.get("percentage") or {}
            pct     = _num(pct_obj.get("raw") if isinstance(pct_obj, dict) else pct_obj)
            h_obj   = ev.get("high") or {}
            l_obj   = ev.get("low") or {}
            hi      = _num(h_obj.get("raw") if isinstance(h_obj, dict) else h_obj)
            lo      = _num(l_obj.get("raw") if isinstance(l_obj, dict) else l_obj)
            rows.append((symbol, as_of, period, pct, hi, lo))
        if rows:
            conn.executemany(
                "INSERT INTO price_performance VALUES (?,?,?,?,?,?)", rows
            )
        return True
    except Exception as e:
        print(f"    price_perf: {e}")
        return False


def scrape_corp_actions(client, symbol: str, conn) -> int:
    # CorporateAction model fields: action_type, announcement_date, ex_date,
    # description. Dividend subclass adds: dividend_amount, payment_date.
    try:
        actions = client.corporate_actions.get_by_symbol(symbol)
        if not actions:
            return 0
        conn.execute("DELETE FROM corporate_actions WHERE symbol = ?", [symbol])
        rows = []
        for a in (actions if isinstance(actions, list) else [actions]):
            av       = _model_to_dict(a)
            atype    = av.get("action_type") or ""
            # Real data nested in action_info[action_type] dict
            info_raw = av.get("action_info") or {}
            info     = info_raw.get(atype, {}) if isinstance(info_raw, dict) else {}
            # Field names differ per action type — dividend, rups, stock_split...
            ann_date = _date(
                info.get("dividend_created") or info.get("announcement_date")
                or av.get("announcement_date")
            )
            ex_date  = _date(
                info.get("dividend_exdate") or info.get("ex_date")
                or av.get("ex_date")
            )
            pay_date = _date(
                info.get("dividend_paydate") or info.get("payment_date")
            )
            cash     = _num(info.get("dividend_value") or info.get("cash_amount"))
            rows.append((
                symbol, atype, ann_date, ex_date, pay_date,
                None,  # ratio (splits handled separately if needed)
                cash,
                info.get("event_note") or av.get("description") or "",
            ))
        if rows:
            conn.executemany(
                "INSERT INTO corporate_actions VALUES (?,?,?,?,?,?,?,?)", rows
            )
        return len(rows)
    except Exception as e:
        print(f"    corp_actions: {e}")
        return 0


def scrape_company_info(client, symbol: str, conn) -> bool:
    try:
        info = client.company.get_info(symbol)
        if not info:
            return False
        iv = info if isinstance(info, dict) else vars(info)
        conn.execute("""
            INSERT INTO stocks (symbol, name, sector, industry, listing_date,
                                shares_outstanding, description)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT (symbol) DO UPDATE SET
                name=excluded.name, sector=excluded.sector,
                industry=excluded.industry, description=excluded.description
        """, [
            symbol,
            _val(iv, "name") or _val(iv, "company_name"),
            _val(iv, "sector"),
            _val(iv, "industry") or _val(iv, "subsector"),
            _date(_val(iv, "listing_date") or _val(iv, "ipo_date")),
            _val(iv, "shares_outstanding") or _val(iv, "outstanding_shares"),
            _val(iv, "description") or _val(iv, "about") or "",
        ])
        return True
    except Exception as e:
        print(f"    company info: {e}")
        return False


# ---------------------------------------------------------------------------
# Main scrape loop
# ---------------------------------------------------------------------------

def run_scrape(
    symbols: List[str],
    db_path: str,
    token: str,
    days: int = 90,
    sleep_ms: int = 200,
    log_path: Optional[str] = None,
) -> None:
    import duckdb
    from stockbit import StockbitClient
    from market.schema import create_schema

    today  = date.today()
    since  = (today - timedelta(days=days)).isoformat()
    until  = today.isoformat()
    as_of  = today

    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn   = duckdb.connect(db_path)
    create_schema(conn)

    # Optional log file for progress tracking
    log_f  = open(log_path, "a", buffering=1) if log_path else None

    def log(msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        if log_f:
            log_f.write(line + "\n")
            log_f.flush()

    client = StockbitClient(token=token)
    log(f"START scraping {len(symbols)} symbols  {since} -> {until}")

    for i, sym in enumerate(symbols, 1):
        t0 = time.time()
        log(f"[{i}/{len(symbols)}] {sym} ...")

        ok_co   = scrape_company_info(client, sym, conn)
        time.sleep(sleep_ms / 1000)

        n_ohlcv = scrape_ohlcv(client, sym, conn, since, until)
        time.sleep(sleep_ms / 1000)

        scrape_ratios(client, sym, conn, as_of)
        time.sleep(sleep_ms / 1000)

        n_fin = scrape_financials(client, sym, conn)
        time.sleep(sleep_ms / 1000)

        scrape_analyst(client, sym, conn, as_of)
        time.sleep(sleep_ms / 1000)

        scrape_price_perf(client, sym, conn, as_of)
        time.sleep(sleep_ms / 1000)

        n_act = scrape_corp_actions(client, sym, conn)
        time.sleep(sleep_ms / 1000)

        conn.execute("CHECKPOINT")

        elapsed = time.time() - t0
        log(f"  done  ohlcv={n_ohlcv}  fin_rows={n_fin}  actions={n_act}  {elapsed:.1f}s")

    client.close()
    conn.close()
    log("DONE")
    if log_f:
        log_f.close()
    size_mb = os.path.getsize(db_path) / 1_048_576
    print(f"\nDone — {os.path.basename(db_path)}  {size_mb:.1f} MB")
