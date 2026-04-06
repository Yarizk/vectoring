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
from rag import ask, ask_with_metadata_filter, check_ollama, check_jatevo, list_available_models
from rag_enhanced import ask_enhanced, RESPONSE_MODES, analyze_data_quality, generate_enhanced_prompt
from ingest_json import ingest_all_json_files
from ingest_pdf import ingest_all_pdfs
from config import LLM_PROVIDER, JATEVO_BASE_URL, JATEVO_MODEL, validate_config

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
        status = "healthy" if not errors else "degraded"
    else:
        provider_ok = check_ollama()
        status = "healthy" if provider_ok else "degraded"
    
    return {
        "status": status,
        "provider": LLM_PROVIDER,
        "provider_connected": provider_ok,
        "config_errors": errors
    }


@app.get("/stats", response_model=StatsResponse)
def stats():
    """Get database and system statistics."""
    db_stats = get_stats()
    errors = validate_config()
    
    ollama_ok = check_ollama() if LLM_PROVIDER == "ollama" else False
    jatevo_ok = check_jatevo() if LLM_PROVIDER == "jatevo" else False
    
    # Get available models based on provider
    models = []
    if LLM_PROVIDER == "ollama" and ollama_ok:
        models = list_available_models()
    elif LLM_PROVIDER == "jatevo":
        models = [JATEVO_MODEL]
    
    return StatsResponse(
        collection_name=db_stats["collection_name"],
        document_count=db_stats["document_count"],
        embedding_model=db_stats["embedding_model"],
        chroma_db_path=db_stats["chroma_db_path"],
        llm_provider=LLM_PROVIDER,
        ollama_status=ollama_ok,
        jatevo_status=jatevo_ok,
        jatevo_model=JATEVO_MODEL,
        available_models=models,
        config_errors=errors
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
        error=result.get("error")
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
