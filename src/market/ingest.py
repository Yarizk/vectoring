"""
CLI entrypoint for market data ingestion pipeline.

Usage:
    cd src && python -m market.ingest [--symbols BBRI BBCA ...] [--days 90] [--no-embed] [--embed-only]

Scrapes Stockbit API -> DuckDB, then embeds into ChromaDB.
"""

from __future__ import annotations

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.dirname(_HERE)
_PROJECT = os.path.dirname(_SRC)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# Default watchlist: IDX LQ45 + major liquid stocks + IDX80 expansion
DEFAULT_SYMBOLS = [
    # Original LQ45 + liquid watchlist
    "AALI", "ADRO", "AKRA", "AMRT", "ANTM", "ARTO", "ASII", "BBCA", "BBNI",
    "BBRI", "BBTN", "BMRI", "BRIS", "BRPT", "BSDE", "CPIN", "EMTK", "ERAA",
    "ESSA", "EXCL", "GGRM", "GOTO", "HRUM", "ICBP", "INCO", "INDF", "INTP",
    "ISAT", "ITMG", "JSMR", "KLBF", "MAPI", "MBMA", "MDKA", "MEDC", "MIKA",
    "MNCN", "PGAS", "PGEO", "PTBA", "PTPP", "SMGR", "SMRA", "TAPG", "TBIG",
    "TINS", "TLKM", "TOWR", "UNTR", "UNVR", "SIDO", "WIFI", "BFIN", "DSSA",
    "CTRA", "JPFA", "HEAL", "ADMR", "FILM", "NICE",
    # IDX80 expansion
    "HMSP", "PWON", "PNBN", "SCCO", "KBLI", "TSPC", "INDY", "DNET", "BREN",
    "INKP", "TKIM", "WSKT", "SSIA", "ELSA", "ADHI", "ADMF", "PPRE", "NCKL",
    "WTON", "KIJA", "BKSL", "BIRD", "CUAN", "AVIA", "CMPP",
]


def _get_db_path() -> str:
    try:
        from config import MARKET_DB_PATH
        return MARKET_DB_PATH
    except ImportError:
        return os.path.join(_PROJECT, "data", "market.duckdb")


def _get_token() -> str:
    try:
        from config import STOCKBIT_TOKEN
        return STOCKBIT_TOKEN or ""
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(_PROJECT, ".env"))
        return os.getenv("MARKET_DATA_TOKEN", os.getenv("STOCKBIT_TOKEN", ""))


def main():
    parser = argparse.ArgumentParser(description="Market data ingestion pipeline")
    parser.add_argument(
        "--symbols", nargs="+", default=None,
        help="Stock symbols to ingest (default: LQ45 watchlist)"
    )
    parser.add_argument(
        "--days", type=int, default=90,
        help="Days of OHLCV history to fetch (default: 90)"
    )
    parser.add_argument(
        "--no-embed", action="store_true",
        help="Skip ChromaDB embedding (DuckDB only)"
    )
    parser.add_argument(
        "--embed-only", action="store_true",
        help="Skip scraping, only embed existing DuckDB data into ChromaDB"
    )
    parser.add_argument(
        "--db", default=None,
        help="Override DuckDB path (default: data/market.duckdb)"
    )
    parser.add_argument(
        "--sleep-ms", type=int, default=200,
        help="Milliseconds between API calls per symbol (default: 200)"
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Skip symbols already in DuckDB stocks table"
    )
    parser.add_argument(
        "--log", default=None,
        help="Path to write progress log (default: data/ingest.log)"
    )
    args = parser.parse_args()

    db_path  = args.db or _get_db_path()
    token    = _get_token()
    symbols  = args.symbols or DEFAULT_SYMBOLS
    log_path = args.log or os.path.join(_PROJECT, "data", "ingest.log")

    if args.skip_existing and not args.embed_only:
        try:
            import duckdb as _ddb
            _c = _ddb.connect(db_path, read_only=True)
            _done = {r[0] for r in _c.execute("SELECT symbol FROM stocks").fetchall()}
            _c.close()
            before = len(symbols)
            symbols = [s for s in symbols if s not in _done]
            print(f"--skip-existing: {before - len(symbols)} already done, {len(symbols)} remaining: {symbols}")
        except Exception:
            pass  # no DB yet, scrape everything

    if not args.embed_only:
        if not token:
            print("ERROR: No Stockbit token found. Set MARKET_DATA_TOKEN in .env")
            sys.exit(1)
        if not symbols:
            print("All symbols already ingested. Nothing to scrape.")
        else:
            from market.scrapers import run_scrape
            run_scrape(
                symbols=symbols,
                db_path=db_path,
                token=token,
                days=args.days,
                sleep_ms=args.sleep_ms,
                log_path=log_path,
            )

    if not args.no_embed:
        print("\nEmbedding into ChromaDB...")
        from market.embed import embed_all
        results = embed_all(db_path, symbols if args.embed_only else None)
        total = sum(results.values())
        print(f"Embedded {total} total chunks: {results}")

    print("\nDone.")


if __name__ == "__main__":
    main()
