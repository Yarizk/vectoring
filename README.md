# KSEI RAG - Indonesian Stock Ownership RAG System

A Retrieval-Augmented Generation (RAG) system for querying Indonesian stock market ownership data from KSEI (Indonesia Central Securities Depository) using natural language.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  User Query │────▶│  ChromaDB    │────▶│    Qwen     │
│   (React)   │     │  Vector DB   │     │ via Jatevo  │
└─────────────┘     └──────────────┘     └──────┬──────┘
       │                                        │
       │         ┌──────────────────────────────┘
       │         │
       ▼         ▼
┌─────────────────────────┐
│  Answer + Source Citations│
└─────────────────────────┘
```

**Data Flow:**
1. **Ingest**: KSEI PDFs + JSON → ChromaDB (vector embeddings)
2. **Query**: User question → semantic search → retrieve relevant chunks
3. **Generate**: LLM (Qwen 2.5) generates answer based on retrieved context
4. **Cite**: Sources are displayed with each answer

## Features

- 🔍 **Natural Language Queries**: Ask questions in Indonesian or English
- 📊 **Dual Data Sources**: KSEI PDF reports + structured JSON data
- 🎯 **Metadata Filtering**: Filter by ticker symbol, date, source type
- 📚 **Source Citations**: Every answer includes references to source documents
- 🤖 **Dual LLM Support**: Local Ollama (free) or Jatevo API (better performance, default)
- 🎨 **React Frontend**: Bloomberg Terminal aesthetic with rich data visualization
- 🏠 **Privacy-First**: Local embeddings, option for local LLM
- 🐳 **Docker Support**: One-command deployment with docker-compose

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed locally (for local LLM option)
- OR Jatevo API key (for cloud LLM option)
- 8GB+ RAM recommended (for local Ollama)

## Quick Start

### Option 1: Local LLM (Ollama) - Free, Runs Locally

#### 1. Install Ollama and Pull Model

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Qwen 2.5 7B model (~4.4GB)
ollama pull qwen2.5:7b

# Start Ollama server
ollama serve
```

#### 2. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env to use Ollama
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
```

### Option 2: Cloud LLM (Jatevo API) - Better Performance

#### 1. Get API Key

Sign up at [Jatevo](https://jatevo.id) and get your API key.

#### 2. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env to use Jatevo
LLM_PROVIDER=jatevo
JATEVO_API_KEY=your_actual_api_key_here
JATEVO_MODEL=qwen3.5-plus
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Ingest Data

Data files should be placed in:
- `archive/*.json` - KSEI JSON data files
- `raw_data/*.pdf` - KSEI PDF reports

Run ingestion:
```bash
cd src

# Ingest JSON data
python ingest_json.py

# Ingest PDF data
python ingest_pdf.py
```

### 5. Start Services

#### Option A: Development (Hot Reload)

Terminal 1 - API:
```bash
cd src
python api.py
```

Terminal 2 - React Frontend:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

#### Option B: Production

Build and serve from API:
```bash
cd frontend
npm install
npm run build

cd ..
python src/api.py
```

Open http://localhost:8000 in your browser.

## Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- Ollama: http://localhost:11434
- API + Frontend: http://localhost:8000

## API Usage

### Ask a Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Siapa pemegang saham terbesar BBCA?",
    "n_results": 5,
    "temperature": 0.3
  }'
```

### Get Stats

```bash
curl http://localhost:8000/stats
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Example Queries

| Question | Expected Answer |
|----------|-----------------|
| "Siapa pemegang saham terbesar BBRI?" | Danantara Asset Management (52.66%) |
| "Berapa kepemilikan asing di BBCA?" | Foreign ownership percentage |
| "Saham apa yang kepemilikan lokalnya tinggi?" | Stocks with high local ownership |
| "Compare TLKM and EXCL foreign ownership" | Comparison of both stocks |
| "Who is the largest holder of GOTO?" | Top shareholder name and % |

## Project Structure

```
ksei-rag/
├── src/
│   ├── embedder.py      # Embedding + ChromaDB operations
│   ├── ingest_json.py   # JSON data ingestion
│   ├── ingest_pdf.py    # PDF data ingestion
│   ├── rag.py           # Core RAG logic
│   ├── api.py           # FastAPI endpoints
│   ├── search_utils.py  # Hybrid search utilities
│   └── config.py        # Configuration management
├── frontend/            # React frontend
│   ├── src/            # React source code
│   └── package.json    # Node dependencies
├── archive/             # KSEI JSON files
├── raw_data/            # KSEI PDF files
├── chroma_db/           # ChromaDB storage (auto-created)
├── docker-compose.yml   # Docker orchestration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Response Modes

The chatbot supports three response modes to control the balance between factual accuracy and analytical depth:

| Mode | Description | Use When |
|------|-------------|----------|
| **Strict** | Only use retrieved data, no assumptions | You need verified facts only |
| **Balanced** | Data + reasonable connections | You want analysis grounded in data |
| **Explorative** | Broader analysis with confidence markers | You want insights beyond raw data |

### Confidence Markers

The bot marks its responses with confidence indicators:
- **[CERTAIN]** - Fact directly from retrieved data
- **[INFERRED]** - Reasonable conclusion from data
- **[UNCERTAIN]** - Educated guess with limited data
- **[NOT_AVAILABLE]** - Data doesn't exist in context
- **[BEYOND_DATA]** - Analysis going beyond retrieved context (explorative mode only)

### Data Quality Assessment

Each response includes a quality score showing:
- **Relevance Score** (0-100%): How well the retrieved data matches the query
- **Coverage**: complete/partial/minimal/none - how much of the query is covered
- **Gaps**: What's missing from the data
- **Recommendations**: How to improve the query

## Chunking Strategy

The system uses a hybrid chunking approach optimized for financial data:

1. **Ticker Summaries** (`chunk_type: ticker_summary`):
   - One chunk per stock ticker
   - Contains aggregated ownership data
   - Top holders list with percentages
   - Local/Foreign ownership totals

2. **Holder-Focused Chunks** (`chunk_type: holder_focus`):
   - One chunk per significant holder (>1%)
   - Enables investor-specific queries
   - Links holder to ticker + date

3. **PDF Page Chunks** (`chunk_type: pdf_page`):
   - Text extracted from PDF pages
   - Chunked with 800 char size + 100 overlap
   - Preserves page numbers for citations

## Metadata Filtering

You can filter queries by:
- **ticker**: Stock symbol (e.g., "BBCA", "BBRI")
- **date**: Report date (e.g., "2026-03-31")
- **source**: "ksei_json" or "ksei_pdf"
- **chunk_type**: "ticker_summary", "holder_focus", "pdf_page"

Example with filter:
```python
from rag import ask_with_metadata_filter

result = ask_with_metadata_filter(
    question="Siapa pemegang saham terbesar?",
    ticker="BBCA"
)
```

## Troubleshooting

### Ollama Connection Error
```
Error: Cannot connect to Ollama at http://localhost:11434
```
**Fix**: Start Ollama: `ollama serve`

### Model Not Found
```
Error: qwen2.5:7b not found
```
**Fix**: Pull the model: `ollama pull qwen2.5:7b`

### Empty Results
**Check**: Verify data is ingested:
```bash
curl http://localhost:8000/stats
```

### Out of Memory (Ollama only)
**Fix**: Use a smaller model:
```bash
ollama pull qwen2.5:1.8b  # Smaller, faster
```

### Jatevo Authentication Error
```
Error: Authentication failed. Check your JATEVO_API_KEY.
```
**Fix**: 
1. Verify your API key in `.env` file
2. Ensure `LLM_PROVIDER=jatevo` is set
3. Restart the API after changing `.env`

### Jatevo API Connection Error
```
Error: Cannot connect to Jatevo API
```
**Fix**: Check your internet connection and Jatevo service status.

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider: `ollama` or `jatevo` | `jatevo` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `qwen2.5:7b` |
| `JATEVO_BASE_URL` | Jatevo API endpoint | `https://jatevo.id/api/open/v1/inference` |
| `JATEVO_API_KEY` | Your Jatevo API key | (required for Jatevo) |
| `JATEVO_MODEL` | Jatevo model name | `qwen3.5-plus` |

## Performance Notes

- **Embedding**: First run downloads `all-MiniLM-L6-v2` (~80MB)
- **Ingestion**: ~5-10 minutes for 2 months of data
- **Query**: 2-5 seconds per question (depending on model)
- **Storage**: ~500MB per month of data (including embeddings)

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- KSEI for providing ownership data
- Stockbit for market data
- Ollama for local LLM hosting
- ChromaDB for vector storage
