"""
Comparative/ranking queries against DuckDB for cross-stock analysis.
Called when is_comparative_query() is True and query_type is 'market'.
"""

from __future__ import annotations

import os
from typing import Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(os.path.dirname(_HERE))
_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "market.duckdb")

# ── Metric routing ─────────────────────────────────────────────────────────────
# Each entry: (trigger_keywords, column, direction, display_label, table)
# Checked in order — first match wins.
_METRIC_ROUTES = [
    # PE ratio — lowest
    (["pe ratio terendah", "pe terendah", "pe paling rendah", "pe ratio rendah",
      "pe rendah", "lowest pe", "pe ratio lowest", "paling rendah di lq45",
      "ratio paling rendah", "ratio-nya paling rendah"],
     "pe_ttm", "ASC", "PE Ratio (TTM)", "fundamentals_ratio"),
    # PE ratio — highest
    (["pe ratio tertinggi", "pe tertinggi", "pe paling tinggi", "pe ratio tinggi",
      "pe tinggi", "highest pe", "ratio paling tinggi", "ratio-nya paling tinggi"],
     "pe_ttm", "DESC", "PE Ratio (TTM)", "fundamentals_ratio"),
    # PB ratio — lowest
    (["pb ratio terendah", "pb terendah", "pb paling rendah", "lowest pb"],
     "pb", "ASC", "PB Ratio", "fundamentals_ratio"),
    # PB ratio — highest
    (["pb ratio tertinggi", "pb tertinggi", "highest pb"],
     "pb", "DESC", "PB Ratio", "fundamentals_ratio"),
    # ROE — highest
    (["roe tertinggi", "roe terbesar", "roe paling tinggi", "highest roe",
      "roe terbaik"],
     "roe", "DESC", "ROE (%)", "fundamentals_ratio"),
    # ROE — lowest
    (["roe terendah", "roe paling rendah", "lowest roe"],
     "roe", "ASC", "ROE (%)", "fundamentals_ratio"),
    # ROA — highest
    (["roa tertinggi", "highest roa"],
     "roa", "DESC", "ROA (%)", "fundamentals_ratio"),
    # Dividend yield — highest
    (["dividend yield tertinggi", "dividend yield terbesar", "yield tertinggi",
      "yield terbesar", "dividen yield tertinggi", "highest dividend yield",
      "highest yield", "dividend yield paling tinggi"],
     "dividend_yield", "DESC", "Dividend Yield (%)", "fundamentals_ratio"),
    # Dividend yield — lowest
    (["dividend yield terendah", "yield terendah", "lowest dividend yield"],
     "dividend_yield", "ASC", "Dividend Yield (%)", "fundamentals_ratio"),
    # EPS — highest
    (["eps tertinggi", "eps terbesar", "highest eps"],
     "earnings_yield", "DESC", "Earnings Yield (%)", "fundamentals_ratio"),
    # Stock price — highest
    (["harga tertinggi", "harga saham tertinggi", "saham termahal", "highest price",
      "harga paling tinggi", "paling mahal", "termahal"],
     "close", "DESC", "Harga Penutupan (Rp)", "ohlcv_latest"),
    # Stock price — lowest
    (["harga terendah", "harga saham terendah", "saham termurah", "lowest price",
      "paling murah", "termurah", "harga paling rendah"],
     "close", "ASC", "Harga Penutupan (Rp)", "ohlcv_latest"),
]


def run_comparative(query: str, limit: int = 15) -> Optional[str]:
    """
    Match query to a ranking metric and run DuckDB query.
    Returns a formatted ranking table string, or None if no metric matched.
    """
    q = query.lower()

    lq45_filter = "lq45" in q or "lq 45" in q

    matched = None
    for keywords, col, direction, label, table in _METRIC_ROUTES:
        if any(kw in q for kw in keywords):
            matched = (col, direction, label, table)
            break

    if not matched:
        return None

    col, direction, label, table = matched

    try:
        import duckdb
        conn = duckdb.connect(_DB_PATH, read_only=True)

        if table == "fundamentals_ratio":
            sql = f"""
                SELECT fr.symbol, s.name, fr.{col}
                FROM fundamentals_ratio fr
                JOIN (
                    SELECT symbol, MAX(date) AS d
                    FROM fundamentals_ratio
                    GROUP BY symbol
                ) latest ON fr.symbol = latest.symbol AND fr.date = latest.d
                LEFT JOIN stocks s ON s.symbol = fr.symbol
                WHERE fr.{col} IS NOT NULL AND fr.{col} > 0
                ORDER BY fr.{col} {direction}
                LIMIT {limit}
            """
        else:  # ohlcv_latest
            sql = f"""
                SELECT o.symbol, s.name, o.{col}
                FROM ohlcv_daily o
                JOIN (
                    SELECT symbol, MAX(date) AS d
                    FROM ohlcv_daily
                    GROUP BY symbol
                ) latest ON o.symbol = latest.symbol AND o.date = latest.d
                LEFT JOIN stocks s ON s.symbol = o.symbol
                WHERE o.{col} IS NOT NULL
                ORDER BY o.{col} {direction}
                LIMIT {limit}
            """

        rows = conn.execute(sql).fetchall()
        conn.close()

        if not rows:
            return None

        direction_label = "terendah (ASC)" if direction == "ASC" else "tertinggi (DESC)"
        scope = " [LQ45]" if lq45_filter else ""
        lines = [
            f"Ranking {label} {direction_label}{scope} — data dari DuckDB:",
            f"{'No':>3}  {'Symbol':<6}  {'Nama':<30}  {label}",
            "-" * 55,
        ]
        for i, (symbol, name, val) in enumerate(rows, 1):
            name_str = (name or symbol)[:28]
            val_str = f"{val:.2f}" if isinstance(val, float) else str(val or "N/A")
            lines.append(f"{i:>3}.  {symbol:<6}  {name_str:<30}  {val_str}")

        return "\n".join(lines)

    except Exception:
        return None
