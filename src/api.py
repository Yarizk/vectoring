"""
FastAPI backend for KSEI RAG.
Provides endpoints for querying and ingestion.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os

from embedder import get_stats, delete_collection
from rag import check_ollama, check_jatevo, list_available_models
from rag_enhanced import ask_enhanced, RESPONSE_MODES, check_deepseek
from ingest_json import ingest_all_json_files
from ingest_pdf import ingest_all_pdfs
from config import LLM_PROVIDER, JATEVO_MODEL, DEEPSEEK_MODEL, validate_config
from stockbit_enricher import enrich_tickers

# Get the project root directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
FRONTEND_DIST = os.path.join(PROJECT_ROOT, "frontend", "dist")

# Create FastAPI app
app = FastAPI(
    title="KSEI RAG API",
    description="Retrieval-Augmented Generation API for Indonesian stock ownership data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files if they exist
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")
    app.mount("/favicon.svg", StaticFiles(directory=FRONTEND_DIST), name="favicon")


# Request/Response models
class AskRequest(BaseModel):
    question: str
    n_results: int = 5
    temperature: float = 0.3
    ticker: Optional[str] = None
    mode: str = "balanced"  # strict, balanced, explorative
    include_quality: bool = True


class AskResponse(BaseModel):
    question: str
    answer: Optional[str]
    sources: List[Dict[str, Any]]
    quality: Optional[Dict[str, Any]]
    mode: str
    success: bool
    error: Optional[str]
    enrichment: Optional[Dict[str, Any]] = None


class StatsResponse(BaseModel):
    collection_name: str
    document_count: int
    embedding_model: str
    chroma_db_path: str
    llm_provider: str
    ollama_status: bool
    jatevo_status: bool
    jatevo_model: str
    available_models: List[str]
    config_errors: List[str]


class IngestResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]]


# Global ingestion status
ingestion_status = {"running": False, "last_result": None}


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": "KSEI RAG API",
        "version": "1.0.0",
        "endpoints": [
            "/ask - Ask a question",
            "/stats - Get database stats",
            "/health - Health check",
            "/ingest - Trigger data ingestion"
        ]
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    errors = validate_config()

    if LLM_PROVIDER == "jatevo":
        provider_ok = check_jatevo()
    elif LLM_PROVIDER == "deepseek":
        result = check_deepseek()
        provider_ok = result["available"]
        if not result["available"] and result.get("error"):
            errors = errors + [result["error"]]
    else:
        provider_ok = check_ollama()

    status = "healthy" if provider_ok and not errors else "degraded"
    return {
        "status": status,
        "provider": LLM_PROVIDER,
        "provider_connected": provider_ok,
        "config_errors": errors,
    }


@app.get("/stats", response_model=StatsResponse)
def stats():
    """Get database and system statistics."""
    db_stats = get_stats()
    errors = validate_config()

    ollama_ok = check_ollama() if LLM_PROVIDER == "ollama" else False
    jatevo_ok = check_jatevo() if LLM_PROVIDER == "jatevo" else False
    deepseek_ok = check_deepseek()["available"] if LLM_PROVIDER == "deepseek" else False

    models = []
    if LLM_PROVIDER == "ollama" and ollama_ok:
        models = list_available_models()
    elif LLM_PROVIDER == "jatevo":
        models = [JATEVO_MODEL]
    elif LLM_PROVIDER == "deepseek":
        models = [DEEPSEEK_MODEL]

    return StatsResponse(
        collection_name=db_stats["collection_name"],
        document_count=db_stats["document_count"],
        embedding_model=db_stats["embedding_model"],
        chroma_db_path=db_stats["chroma_db_path"],
        llm_provider=LLM_PROVIDER,
        ollama_status=ollama_ok,
        jatevo_status=jatevo_ok or deepseek_ok,
        jatevo_model=DEEPSEEK_MODEL if LLM_PROVIDER == "deepseek" else JATEVO_MODEL,
        available_models=models,
        config_errors=errors,
    )


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest):
    """
    Ask a question about KSEI ownership data.
    
    - **question**: Your question in Indonesian or English
    - **n_results**: Number of context chunks to retrieve (default: 5)
    - **temperature**: Generation temperature 0.0-1.0 (default: 0.3)
    - **ticker**: Optional ticker symbol to filter by
    - **mode**: Response mode - "strict", "balanced", or "explorative"
    - **include_quality**: Include data quality analysis (default: True)
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Validate mode
    if request.mode not in RESPONSE_MODES:
        request.mode = "balanced"
    
    # Use enhanced RAG
    result = ask_enhanced(
        question=request.question,
        mode=request.mode,
        n_results=request.n_results,
        include_quality_analysis=request.include_quality
    )
    
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


@app.get("/modes")
def get_modes():
    """Get available response modes and their descriptions."""
    return {
        "modes": {
            mode: {
                "description": config["description"],
                "temperature": config["temperature"],
                "creativity": config["creativity"],
                "allow_inference": config["allow_inference"],
                "allow_general_knowledge": config["allow_general_knowledge"]
            }
            for mode, config in RESPONSE_MODES.items()
        }
    }


@app.post("/ingest", response_model=IngestResponse)
def ingest_endpoint(
    background_tasks: BackgroundTasks,
    clear_existing: bool = False,
    json_only: bool = False,
    pdf_only: bool = False
):
    """
    Trigger data ingestion.
    
    - **clear_existing**: Clear existing data before ingestion
    - **json_only**: Only ingest JSON files
    - **pdf_only**: Only ingest PDF files
    
    Note: This runs in the background and may take several minutes.
    """
    global ingestion_status
    
    if ingestion_status["running"]:
        return IngestResponse(
            success=False,
            message="Ingestion is already running",
            details=None
        )
    
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
    
    # Run in background
    background_tasks.add_task(do_ingestion)
    
    return IngestResponse(
        success=True,
        message="Ingestion started in background. Check /stats for progress.",
        details={"clear_existing": clear_existing, "json_only": json_only, "pdf_only": pdf_only}
    )


@app.get("/ingest/status")
def ingest_status():
    """Get current ingestion status."""
    return {
        "running": ingestion_status["running"],
        "last_result": ingestion_status["last_result"]
    }


@app.delete("/collection")
def delete_collection_endpoint():
    """Delete the entire ChromaDB collection (use with caution)."""
    success = delete_collection("ksei_data")
    return {
        "success": success,
        "message": "Collection deleted" if success else "Collection not found or error"
    }


# Serve frontend index.html for root and non-API routes
@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the React frontend."""
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "KSEI RAG API", "frontend": "Not built"}

@app.get("/api/ticker/{symbol}")
def get_ticker_enrichment(symbol: str):
    """Get live Stockbit enrichment data for a single ticker."""
    symbol = symbol.upper()
    enrichment = enrich_tickers([symbol])
    data = enrichment.get(symbol, {})
    return {
        "ticker": symbol,
        "enrichment": data,
        "available": bool(data and any(v for v in data.values())),
    }


@app.get("/api/chart/{symbol}/ohlcv")
def get_ohlcv_chart(symbol: str, days: int = 90):
    """Return OHLCV data for candlestick chart from market DuckDB."""
    symbol = symbol.upper()
    try:
        import duckdb
        from config import MARKET_DB_PATH
        from datetime import date, timedelta
        if not os.path.exists(MARKET_DB_PATH):
            return {"ticker": symbol, "data": [], "error": "market.duckdb not found — run market ingestion first"}
        since = (date.today() - timedelta(days=days)).isoformat()
        conn = duckdb.connect(MARKET_DB_PATH, read_only=True)
        rows = conn.execute("""
            SELECT date, open, high, low, close, volume, net_foreign
            FROM ohlcv_daily
            WHERE symbol = ? AND date >= ?
            ORDER BY date ASC
        """, [symbol, since]).fetchall()
        conn.close()
        data = [
            {
                "time": str(r[0]),
                "open": r[1], "high": r[2], "low": r[3], "close": r[4],
                "volume": r[5], "net_foreign": r[6],
            }
            for r in rows
        ]
        return {"ticker": symbol, "days": days, "data": data, "count": len(data)}
    except Exception as e:
        return {"ticker": symbol, "data": [], "error": str(e)}


@app.get("/api/chart/{symbol}/fundamentals")
def get_fundamentals_chart(symbol: str):
    """Return fundamental ratios + financials + analyst data for charts."""
    symbol = symbol.upper()
    try:
        import duckdb
        from config import MARKET_DB_PATH
        if not os.path.exists(MARKET_DB_PATH):
            return {"ticker": symbol, "data": {}, "error": "market.duckdb not found — run market ingestion first"}
        conn = duckdb.connect(MARKET_DB_PATH, read_only=True)

        # Latest ratios row
        ratios_row = conn.execute("""
            SELECT pe_ttm, pe_forward, pe_annualised, pb, ps_ttm, ev_ebitda,
                   roe, roa, roic, gross_margin, operating_margin,
                   debt_equity, current_ratio, interest_coverage,
                   dividend_yield, payout_ratio, earnings_yield
            FROM fundamentals_ratio
            WHERE symbol = ?
            ORDER BY date DESC LIMIT 1
        """, [symbol]).fetchone()
        ratio_cols = [
            "pe_ttm", "pe_forward", "pe_annualised", "pb", "ps_ttm", "ev_ebitda",
            "roe", "roa", "roic", "gross_margin", "operating_margin",
            "debt_equity", "current_ratio", "interest_coverage",
            "dividend_yield", "payout_ratio", "earnings_yield",
        ]
        ratios = dict(zip(ratio_cols, ratios_row)) if ratios_row else {}

        # Quarterly financials (last 4 quarters)
        fin_rows = conn.execute("""
            SELECT period_end, line_item, value
            FROM financials_quarterly
            WHERE symbol = ?
            ORDER BY period_end DESC
            LIMIT 40
        """, [symbol]).fetchall()
        from collections import defaultdict
        fin_by_period: dict = defaultdict(dict)
        for period_end, line_item, value in fin_rows:
            fin_by_period[str(period_end)][line_item] = value
        financials = dict(sorted(fin_by_period.items(), reverse=True)[:4])

        # Analyst consensus
        analyst_row = conn.execute("""
            SELECT consensus_rating, target_median, target_high, target_low,
                   estimate_revision_30d_up, estimate_revision_30d_down
            FROM analyst_consensus
            WHERE symbol = ?
            ORDER BY date DESC LIMIT 1
        """, [symbol]).fetchone()
        analyst = {}
        if analyst_row:
            analyst = {
                "consensus_rating": analyst_row[0],
                "target_median": analyst_row[1],
                "target_high": analyst_row[2],
                "target_low": analyst_row[3],
                "estimate_revision_30d_up": analyst_row[4],
                "estimate_revision_30d_down": analyst_row[5],
            }

        # Individual analyst ratings
        rating_rows = conn.execute("""
            SELECT broker, rating, target_price, analyst_name, as_of_date
            FROM analyst_ratings
            WHERE symbol = ?
            ORDER BY as_of_date DESC
        """, [symbol]).fetchall()
        ratings = [
            {"broker": r[0], "rating": r[1], "target_price": r[2],
             "analyst_name": r[3], "date": str(r[4])}
            for r in rating_rows
        ]

        # Price performance
        perf_rows = conn.execute("""
            SELECT period, change_pct FROM price_performance
            WHERE symbol = ?
            ORDER BY as_of_date DESC
        """, [symbol]).fetchall()
        seen = {}
        for period, chg in perf_rows:
            if period not in seen:
                seen[period] = chg
        performance = seen

        # Corporate actions (last 5)
        action_rows = conn.execute("""
            SELECT action_type, announce_date, ex_date, cash_amount, notes
            FROM corporate_actions
            WHERE symbol = ?
            ORDER BY announce_date DESC LIMIT 5
        """, [symbol]).fetchall()
        actions = [
            {"action_type": r[0], "announce_date": str(r[1]),
             "ex_date": str(r[2]), "cash_amount": r[3], "notes": r[4]}
            for r in action_rows
        ]

        conn.close()
        data = {
            "ratios": ratios,
            "financials": financials,
            "analyst": analyst,
            "ratings": ratings,
            "performance": performance,
            "actions": actions,
        }
        return {"ticker": symbol, "data": data}
    except Exception as e:
        return {"ticker": symbol, "data": {}, "error": str(e)}


@app.post("/ingest/market", response_model=IngestResponse)
def ingest_market_endpoint(
    background_tasks: BackgroundTasks,
    symbols: Optional[str] = None,
    days: int = 90,
    embed_only: bool = False,
):
    """
    Trigger market data ingestion from Stockbit API.
    symbols: comma-separated tickers (default: LQ45 watchlist)
    days: days of OHLCV history (default: 90)
    embed_only: skip scraping, only embed existing DuckDB
    """
    global ingestion_status

    if ingestion_status["running"]:
        return IngestResponse(
            success=False,
            message="Ingestion already running",
            details=None,
        )

    sym_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None

    def do_market_ingest():
        ingestion_status["running"] = True
        try:
            from market.ingest import DEFAULT_SYMBOLS, _get_token
            from config import MARKET_DB_PATH
            syms  = sym_list or DEFAULT_SYMBOLS
            token = _get_token()
            if not embed_only:
                from market.scrapers import run_scrape
                run_scrape(symbols=syms, db_path=MARKET_DB_PATH, token=token, days=days)
            from market.embed import embed_all
            result = embed_all(MARKET_DB_PATH, syms if embed_only else None)
            ingestion_status["last_result"] = {"market": result}
        except Exception as e:
            ingestion_status["last_result"] = {"market": {"error": str(e)}}
        finally:
            ingestion_status["running"] = False

    background_tasks.add_task(do_market_ingest)
    return IngestResponse(
        success=True,
        message="Market ingestion started in background. Check /ingest/status for progress.",
        details={"symbols": sym_list or "default watchlist", "days": days, "embed_only": embed_only},
    )


@app.get("/{full_path:path}")
async def serve_frontend_catch_all(full_path: str):
    """Serve the React frontend for all non-API routes."""
    # Don't catch API routes
    if full_path.startswith("docs") or full_path.startswith("openapi"):
        return {"detail": "Not found"}
    
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"detail": "Not found"}


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI server."""
    uvicorn.run("api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    import sys
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"Starting KSEI RAG API on port {port}...")
    print(f"API docs available at: http://localhost:{port}/docs")
    run_server(port=port)
