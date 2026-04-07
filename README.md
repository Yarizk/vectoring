# KSEI Intelligence

A **Retrieval-Augmented Generation (RAG)** system for querying Indonesian stock market ownership data from KSEI (Indonesia Central Securities Depository). Ask questions in natural language — Indonesian or English — and get answers grounded in real ownership data, enriched with live market context from Stockbit.

---

## Screenshots

### Chat Interface
The main chat view uses a Bloomberg Terminal-inspired dark theme with IBM Plex Sans typography, three response mode selectors (Strict / Balanced / Explorative), and inline source citations.

```
┌─────────────────────────────────────────────────────────────────────┐
│  [≡] KSEI Intelligence   [Chat] [Pipeline] [Dashboard]    [⊞]      │  ← 40px header
├──────────────┬─────────────────────────────────┬────────────────────┤
│ Search hist. │                                 │ Sources (3)        │
│              │  You                            │  #1 BBCA · 96%    │
│ Today        │  Siapa pemegang terbesar BBCA?  │  #2 BBCA · 91%    │
│ > Siapa...   │                                 │  #3 BBCA · 88%    │
│              │  KSEI Intelligence  0.3s        │                    │
│ Quick        │  ┌─ BBCA ─ live ──────────┐    │                    │
│ Actions      │  │ Net Buy: Rp 1.2T       │    │                    │
│              │  │ 1W +0.8% 1M +3.2% ...  │    │                    │
│ [Trash]      │  └────────────────────────┘    │                    │
│              │  [CERTAIN] Kepemilikan...       │                    │
│              │                                 │                    │
│              ├─────────────────────────────────┤                    │
│              │ Ask a question...        [Send] │                    │
│              │ [Strict] [Balanced] [Explorative│                    │
└──────────────┴─────────────────────────────────┴────────────────────┘
```

### Response Modes
| Mode | Behavior | Temperature |
|------|----------|-------------|
| **Strict** | Facts from retrieved data only, no inference | 0.1 |
| **Balanced** | Data + reasonable connections, marks inferences | 0.3 |
| **Explorative** | Broader analysis, confidence markers throughout | 0.5 |

---

## What's Been Built

### Core RAG System
- **Hybrid search** — ticker extraction from queries + metadata-filtered ChromaDB lookup + semantic fallback
- **Three response modes** (strict/balanced/explorative) with temperature control
- **Confidence markers** — `[CERTAIN]`, `[INFERRED]`, `[UNCERTAIN]`, `[NOT_AVAILABLE]`, `[BEYOND_DATA]` inline in responses
- **Data quality scoring** — relevance %, coverage assessment, gap analysis per response
- **Bilingual** — handles queries in both Indonesian and English

### Stockbit Integration (Two-Layer Enrichment)
1. **Static layer** — periodic ingestion of company profiles, financial ratios (P/E, P/B, ROE, ROA), analyst consensus, and major holders into ChromaDB alongside KSEI data
2. **Dynamic layer** — live per-query fetch of foreign flow, price performance (1W/1M/3M/6M/YTD/1Y), and corporate actions injected directly into the LLM prompt

### Data Pipeline
```
archive/*.json  ──────┐
                      ├──▶  embedder.py  ──▶  ChromaDB (ksei_data)
raw_data/*.pdf  ──────┘
                               │
stockbit API  ──▶  stockbit_ingest.py ──▶  ChromaDB (company_profile,
                                            financial_ratios, analyst_consensus,
                                            major_holders_stockbit chunks)
```

### Query Pipeline
```
User question
    │
    ├──▶  search_utils.py  ──▶  ticker extraction
    │                            hybrid ChromaDB search
    │
    ├──▶  stockbit_enricher.py  ──▶  live foreign flow + price perf + corp actions
    │
    ├──▶  rag_enhanced.py  ──▶  prompt assembly (context + enrichment + mode)
    │
    └──▶  LLM (Jatevo qwen3.5-plus / Ollama qwen2.5:7b)
              │
              └──▶  Answer + sources + quality score + enrichment data
```

### Frontend
Bloomberg Terminal-inspired React app with:
- **IBM Plex Sans** body font + **IBM Plex Mono** for code/data
- Three-panel layout: session history sidebar / chat / sources panel
- **MarketContext cards** — per-ticker live data block shown above each AI response
- Compact information-dense design (40px header, 4px scrollbar, tight padding throughout)
- Source citations with relevance %, expandable quality inspector
- Quick action buttons that trigger full API calls

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ask` | RAG query with enrichment |
| `GET` | `/api/ticker/{symbol}` | Live enrichment for a single ticker |
| `GET` | `/modes` | Available response modes |
| `GET` | `/stats` | ChromaDB collection stats |
| `GET` | `/health` | API + LLM connectivity check |
| `POST` | `/ingest` | Trigger background data ingestion |
| `GET` | `/ingest/status` | Ingestion job status |

---

## Tech Stack

### Backend
| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| API Framework | FastAPI + Uvicorn |
| Vector DB | ChromaDB (local, persistent) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local) |
| LLM (primary) | Jatevo API — `qwen3.5-plus` |
| LLM (fallback) | Ollama — `qwen2.5:7b` (local) |
| Market data | Stockbit Python client (custom) |
| PDF parsing | pdfplumber |
| Config | python-dotenv + pydantic-settings |

### Frontend
| Layer | Technology |
|-------|------------|
| Framework | React 19 + TypeScript |
| Build tool | Vite 6 |
| Styling | Tailwind CSS 3 |
| State | Zustand 5 (with localStorage persistence) |
| Routing | React Router 7 |
| Table | TanStack Table 8 |
| Markdown | react-markdown + remark-gfm |
| Icons | lucide-react |
| Font | IBM Plex Sans / IBM Plex Mono (Google Fonts) |

### Infrastructure
| Component | Technology |
|-----------|------------|
| Container | Docker + docker-compose |
| Serving | FastAPI static files (React build) |
| Dev proxy | Vite → `localhost:8000` |

---

## Project Structure

```
vectoring/
├── src/
│   ├── api.py                # FastAPI app, all endpoints
│   ├── config.py             # Env-based config (LLM provider, tokens)
│   ├── embedder.py           # sentence-transformers + ChromaDB ops
│   ├── ingest_json.py        # KSEI JSON → ChromaDB chunks
│   ├── ingest_pdf.py         # KSEI PDF → ChromaDB chunks
│   ├── rag.py                # Basic RAG pipeline
│   ├── rag_enhanced.py       # Enhanced RAG (modes, quality, enrichment)
│   ├── search_utils.py       # Hybrid search + ticker extraction
│   ├── stockbit_enricher.py  # Live Stockbit query-time enrichment
│   └── stockbit_ingest.py    # Periodic Stockbit data ingestion
├── stockbit/                 # Stockbit Python client library
│   ├── client.py             # Main client
│   ├── api/                  # API modules (company, financials, quotes…)
│   └── models/               # Pydantic response models
├── tests/
│   ├── conftest.py           # Shared fixtures (mock Stockbit responses)
│   ├── test_config.py
│   ├── test_rag_integration.py
│   ├── test_stockbit_enricher.py
│   └── test_stockbit_ingest.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/         # ChatContainer, AIMessage, MarketContext…
│   │   │   ├── layout/       # Header, LeftSidebar, RightPanel…
│   │   │   └── ui/           # KseiLogo SVG component
│   │   ├── hooks/            # useChat, useTicker, usePipeline
│   │   ├── stores/           # Zustand stores (chat, ui, pipeline)
│   │   ├── types/            # TypeScript interfaces
│   │   └── lib/              # api.ts, utils, constants
│   └── public/
│       └── favicon.svg       # Custom chart-mark favicon
├── archive/                  # KSEI JSON data files (gitignored)
├── raw_data/                 # KSEI PDF reports (gitignored)
├── chroma_db/                # Vector DB storage (gitignored)
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Jatevo API key **or** Ollama installed locally
- Stockbit account token (optional — for live market enrichment)

### 1. Clone and configure

```bash
git clone https://github.com/Yarizk/vectoring.git
cd vectoring

cp .env.example .env
# Edit .env — set LLM_PROVIDER, JATEVO_API_KEY, STOCKBIT_TOKEN
```

### 2. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 3. Ingest data

Place files in `archive/` (JSON) and `raw_data/` (PDF), then:

```bash
cd src

python ingest_json.py   # KSEI ownership JSON
python ingest_pdf.py    # KSEI monthly PDF reports
```

Optionally ingest Stockbit enrichment data into ChromaDB:

```bash
python stockbit_ingest.py   # company profiles, ratios, consensus
```

### 4. Run

**Development** (hot reload):
```bash
# Terminal 1 — API
cd src && python api.py

# Terminal 2 — Frontend
cd frontend && npm install && npm run dev
# Open http://localhost:5173
```

**Production** (single server on :8000):
```bash
cd frontend && npm run build && cd ..
python src/api.py
# Open http://localhost:8000
```

**Docker**:
```bash
docker-compose up -d
# Open http://localhost:8000
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `jatevo` | `jatevo` or `ollama` |
| `JATEVO_API_KEY` | — | Required for Jatevo |
| `JATEVO_MODEL` | `qwen3.5-plus` | Jatevo model ID |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Ollama model |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model |
| `CHROMA_DB_PATH` | `./chroma_db` | Vector DB storage path |
| `STOCKBIT_TOKEN` | — | Optional — enables live market enrichment |
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API port |

---

## Example Queries

```
Siapa pemegang saham terbesar BBRI?
→ Danantara Asset Management dengan 52.66%

Berapa kepemilikan asing di BBCA?
→ [CERTAIN] 43.2% berdasarkan data KSEI Maret 2026

Compare foreign ownership: TLKM vs EXCL
→ Side-by-side comparison with source citations

GOTO top 5 holders?
→ Structured list with names and percentages

Saham apa yang kepemilikan lokalnya meningkat bulan ini?
→ Analysis with data quality score and coverage report
```

---

## Data Chunk Types in ChromaDB

All stored in the `ksei_data` collection:

| `chunk_type` | Source | Content |
|---|---|---|
| `ticker_summary` | KSEI JSON | Per-stock aggregated ownership totals |
| `holder_focus` | KSEI JSON | Individual holder >1% linked to ticker+date |
| `pdf_page` | KSEI PDF | 800-char text chunks from monthly reports |
| `company_profile` | Stockbit | Sector, market cap, description |
| `financial_ratios` | Stockbit | P/E, P/B, ROE, ROA, dividend yield |
| `analyst_consensus` | Stockbit | Buy/Hold/Sell counts, price target |
| `major_holders_stockbit` | Stockbit | Institutional holder details |

---

## What's Next

### High Priority
- [ ] **Authentication** — user accounts, per-user chat history persistence
- [ ] **Streaming responses** — SSE/WebSocket for token-by-token output instead of waiting for full response
- [ ] **Date-range filtering** — UI controls to scope queries to specific months
- [ ] **Ticker autocomplete** — typeahead suggestions in the chat input

### Data & Enrichment
- [ ] **More KSEI data** — ingest 12+ months of history for trend analysis
- [ ] **Scheduled ingestion** — cron job to auto-update ChromaDB when new KSEI files are released
- [ ] **Stockbit websocket** — real-time price streaming into the MarketContext cards
- [ ] **Corporate actions calendar** — dedicated view for upcoming ex-dates and dividends

### UX
- [ ] **Export** — download conversation as PDF/CSV
- [ ] **Comparison view** — side-by-side ticker analysis panel
- [ ] **Ownership chart** — visual bar/pie chart for top holders inline in responses
- [ ] **Session persistence** — persist chat to backend so history survives browser refresh

### Infrastructure
- [ ] **Rate limiting** — protect the API from abuse
- [ ] **Response caching** — cache repeated identical queries to reduce LLM cost
- [ ] **Observability** — structured logging, latency metrics per endpoint
- [ ] **CI/CD** — GitHub Actions for lint + test on push

---

## Troubleshooting

**Ollama not running**
```
Error: Cannot connect to Ollama at http://localhost:11434
Fix: ollama serve
```

**Empty search results**
```
curl http://localhost:8000/stats
# If document_count is 0, run ingest_json.py / ingest_pdf.py first
```

**Jatevo auth failure**
```
Error: Authentication failed
Fix: Check JATEVO_API_KEY in .env, restart API after editing
```

**Frontend 404 on /api routes**
```
Dev mode: Vite proxies /api → localhost:8000 (see vite.config.ts)
Production: FastAPI serves both API and static files from port 8000
```

---

## License

MIT
