# KSEI Intelligence

A RAG (Retrieval-Augmented Generation) system for querying Indonesian stock ownership data from KSEI. Ask questions in natural language — Indonesian or English — and get answers grounded in real data with source citations.

---

## Screenshots

**Empty state — quick action cards**

![Empty state](screenshots/01-empty-state.png)

**Response with source citations and confidence markers**

![Chat response](screenshots/03-response-top.png)

---

## How It Works

```
User question
    │
    ├── ChromaDB semantic search  (local vector DB)
    ├── Live market data fetch    (optional enrichment)
    │
    └── LLM prompt assembly
            │
            └── Answer + sources + quality score
```

Data is ingested from KSEI JSON files and PDF reports into ChromaDB as vector embeddings. On each query, relevant chunks are retrieved and passed to an LLM along with optional live market data enrichment injected directly into the prompt.

Three response modes control LLM behavior:

| Mode | Behavior |
|------|----------|
| **Strict** | Only retrieved data, no inference |
| **Balanced** | Data + light reasoning, marks inferences |
| **Explorative** | Broader analysis with confidence markers |

---

## Stack

**Backend** — Python, FastAPI, ChromaDB, sentence-transformers (`all-MiniLM-L6-v2`), pdfplumber

**LLM** — Cloud LLM API (primary) · Ollama local model (fallback)

**Frontend** — React 19, TypeScript, Vite, Tailwind CSS, Zustand

---

## Setup

```bash
git clone https://github.com/Yarizk/vectoring.git
cd vectoring

# Configure
cp .env.example .env
# Set LLM_PROVIDER, API key, and optional market data token

# Install
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Ingest data (place files in archive/ and raw_data/ first)
cd src && python ingest_json.py && python ingest_pdf.py && cd ..

# Run
cd src && python api.py          # API on :8000
cd frontend && npm run dev       # UI on :5173 (proxies to :8000)
```

Or with Docker:

```bash
docker-compose up -d
# Open http://localhost:8000
```

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ask` | Query with RAG |
| `GET` | `/stats` | DB stats |
| `GET` | `/health` | Health check |
| `POST` | `/ingest` | Trigger ingestion |

Example:

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Siapa pemegang saham terbesar BBCA?", "mode": "balanced"}'
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `jatevo` | `jatevo` or `ollama` |
| `JATEVO_API_KEY` | — | API key for cloud LLM |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Local model name |
| `CHROMA_DB_PATH` | `./chroma_db` | Vector DB path |
| `MARKET_DATA_TOKEN` | — | Optional live market enrichment |

---

## What's Next

- [ ] Streaming responses (SSE)
- [ ] Date-range query filters
- [ ] Scheduled auto-ingestion
- [ ] Real-time price data via WebSocket
- [ ] Ownership trend charts inline in responses
- [ ] Export conversation as PDF

---

## License

MIT
