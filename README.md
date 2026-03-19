# VerdictAI ⚖️

A production-grade Legal RAG (Retrieval-Augmented Generation) system for searching and querying Indian court judgments using semantic search, hybrid metadata filtering, and local LLM-powered answers.

---

## What It Does

Upload court judgment files → ask legal questions in plain English → get grounded answers with source citations from real judgments.

```
Upload ZIP of judgments
        ↓
Chunk → Embed → Store (PostgreSQL + pgvector)
        ↓
Query → Hybrid Search → Ollama LLM → Grounded Answer + Sources
```

---

## Features

- **Batch ingestion** — Upload a ZIP of JSON judgment files, all processed in parallel
- **Hybrid search** — Vector similarity + metadata filters (court, domain, judgment ID, date, bench)
- **RAG answers** — Optional LLM-powered answers grounded strictly in retrieved chunks
- **Multiple ingestion modes** — ZIP batch, single file upload, or direct JSON API
- **Persistent storage** — PostgreSQL + pgvector, survives restarts
- **Simple frontend** — React UI as a replacement for Swagger UI
- **Local LLM** — Ollama llama3.1:8b, no external API calls

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Gateway | FastAPI |
| Chunking | Character chunking with overlap |
| Embeddings | BAAI/bge-large-en-v1.5 (1024-dim) |
| Vector Store | PostgreSQL + pgvector |
| LLM | Ollama llama3.1:8b (local) |
| Frontend | React + Vite |
| Config | pydantic-settings + .env |

---

## Project Structure

```
verdictai/
├── app/
│   ├── core/
│   │   └── config.py          # Service URLs, Ollama config
│   ├── database/
│   │   └── config.py          # PostgreSQL connection
│   ├── routes/
│   │   ├── ingest.py          # Ingestion endpoints
│   │   └── search.py          # Search endpoints
│   └── services/
│       ├── gateway.py         # Entry point (port 8000)
│       ├── chunker.py         # Text chunking (port 8001)
│       ├── embed.py           # Embedding service (port 8002)
│       ├── store.py           # PostgreSQL store (port 8003)
│       └── search.py          # Search + RAG (port 8004)
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── main.jsx
├── testdata/                  # Sample judgment files
├── .env                       # Environment variables (not committed)
├── .env.example               # Template for env setup
├── main.py                    # Starts all 5 services
└── README.md
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL with pgvector extension
- Ollama with llama3.1:8b pulled

```bash
# Pull the LLM model
ollama pull llama3.1:8b
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/verdictai.git
cd verdictai
```

### 2. Create virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Services
CHUNKER_URL=http://localhost:8001
EMBED_URL=http://localhost:8002
STORE_URL=http://localhost:8003
SEARCH_URL=http://localhost:8004

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=legal_db
DB_USER=postgres
DB_PASSWORD=yourpassword
```

### 4. Set up PostgreSQL

```sql
CREATE DATABASE legal_db;
\c legal_db
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE legal_chunks (
    chunk_id            TEXT PRIMARY KEY,
    document_id         TEXT NOT NULL,
    chunk_text          TEXT NOT NULL,
    chunk_index         INTEGER NOT NULL,
    filename            TEXT NOT NULL,
    ingestion_timestamp TEXT NOT NULL,
    judgment_id         TEXT NOT NULL,
    court               TEXT NOT NULL,
    court_level         TEXT NOT NULL,
    decision_date       TEXT NOT NULL,
    domain              TEXT NOT NULL,
    bench               TEXT,
    jurisdiction        TEXT,
    embedding           vector(1024)
);
```

### 5. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Running the App

### Start all backend services (one command)

```bash
python main.py
```

This starts all 5 services simultaneously:

```
Gateway:  http://localhost:8000
Chunker:  http://localhost:8001
Embed:    http://localhost:8002  ← takes ~20s to load model
Store:    http://localhost:8003
Search:   http://localhost:8004
```

> Wait 20-30 seconds for the embedding model to load before making requests.

### Start the frontend

```bash
cd frontend
npm run dev
```

Frontend runs at `http://localhost:5173`

---

## API Reference

### Ingestion

#### Ingest from ZIP (recommended for bulk)
```
POST /ingest/batch
Content-Type: multipart/form-data

zip_file: <your-zip-file.zip>
chunk_size: 800   (optional, default 800)
overlap: 200      (optional, default 200)
```

Expected ZIP structure:
```
judgments.zip
├── IN-HC-ALL-2006-CV-121D60.json
├── IN-HC-BOM-2002-CV-F45D20.json
└── ...
```

Each JSON file format:
```json
{
  "judgment_id": "IN-HC-ALL-2006-CV-121D60",
  "text": "full judgment text...",
  "metadata": {
    "court": "Allahabad High Court",
    "court_level": "HC",
    "decision_date": "27 MARCH, 2006",
    "bench": "Justice Shishir Kumar",
    "jurisdiction": "India"
  },
  "classification": {
    "domain": "service"
  }
}
```

#### Check ingestion job status
```
GET /ingest/jobs/{job_id}
```

Response while processing:
```json
{
  "status": "processing",
  "total_cases": 834,
  "succeeded_so_far": 120,
  "failed_so_far": 3,
  "progress": "120/834"
}
```

---

### Search

```
POST /search/
Content-Type: application/json
```

#### Basic semantic search
```json
{
  "query": "Is a temporary employee entitled to pension after 26 years?",
  "top_k": 5
}
```

#### Hybrid search with filters
```json
{
  "query": "bail application accused in custody",
  "top_k": 5,
  "domain": "criminal",
  "court": "Allahabad High Court",
  "court_level": "HC",
  "decision_date": "27 MARCH, 2006",
  "judgment_id": "IN-HC-ALL-2006-CV-121D60",
  "bench": "Shishir Kumar"
}
```

#### RAG answer with LLM
```json
{
  "query": "Is a temporary government employee entitled to pension after 26 years of service?",
  "top_k": 3,
  "domain": "service",
  "use_llm": true
}
```

Response with `use_llm: true`:
```json
{
  "query": "...",
  "results": [...],
  "answer": "Based on Source 1 (Allahabad High Court, 2006), a temporary government employee who has rendered 26 years of continuous service is entitled to pension under Fundamental Rule 56(e)...",
  "sources_used": [
    {
      "judgment_id": "IN-HC-ALL-2006-CV-121D60",
      "court": "Allahabad High Court",
      "decision_date": "27 MARCH, 2006",
      "score": 0.8047
    }
  ]
}
```

#### Available search filters

| Filter | Type | Example |
|---|---|---|
| `court` | string | `"Allahabad High Court"` |
| `court_level` | string | `"HC"` or `"SC"` |
| `domain` | string | `"service"`, `"criminal"`, `"civil"` |
| `decision_date` | string | `"27 MARCH, 2006"` |
| `judgment_id` | string | `"IN-HC-ALL-2006-CV-121D60"` |
| `bench` | string | `"Shishir Kumar"` |
| `use_llm` | boolean | `true` or `false` |

---

### Store (direct access)

```
GET /documents              # all ingested documents summary
GET /chunks                 # all chunks with vectors
GET /chunks/{document_id}   # chunks for a specific document
```

---

## Health Checks

```
GET http://localhost:8000/health   # gateway
GET http://localhost:8001/health   # chunker
GET http://localhost:8002/health   # embed
GET http://localhost:8003/health   # store
GET http://localhost:8004/health   # search
```

---

## Dataset Format

Built for Indian court judgment JSONs with the following structure. Each file contains the full judgment text and extracted metadata. Tested with 834 real High Court and Supreme Court judgments.

Supported domains: `service`, `civil`, `criminal`, `mixed`
Supported court levels: `HC` (High Court), `SC` (Supreme Court)

---

## How It Works

### Ingestion Pipeline
```
ZIP upload
    ↓
parse_json_zip() — reads each JSON, extracts text + metadata
    ↓
chunker service — splits text into 800-char chunks with 200-char overlap
    ↓
embed service — BAAI/bge-large-en-v1.5 → 1024-dim vectors (batched in 20s)
    ↓
store service — INSERT INTO legal_chunks (PostgreSQL + pgvector)
```

### Search Pipeline
```
User query
    ↓
embed service — query text → 1024-dim vector
    ↓
store service — SELECT all chunks
    ↓
metadata filters — court, domain, date etc. (in Python)
    ↓
cosine similarity — rank filtered chunks
    ↓
[optional] Ollama llama3.1:8b — generate grounded answer from top-k chunks
```

---

## Known Limitations

- Search loads all chunks into memory (works for ~834 cases, needs pgvector native ANN search for 10k+ cases)
- Job status resets on gateway restart (in-memory dict, no Redis yet)
- Character-based chunking can split mid-word on boundaries
- Bench field from dataset is very long and gets truncated to 200 chars

---

## Roadmap

- [ ] pgvector native HNSW index for in-database ANN search
- [ ] Cross-encoder reranking (ms-marco)
- [ ] Hybrid BM25 + vector search
- [ ] Redis for persistent job tracking
- [ ] Streaming LLM responses
- [ ] Unstructured.io for scanned PDF / image support
- [ ] RAGAS evaluation pipeline
- [ ] LangChain migration (v2)

---

## Environment Variables Reference

| Variable | Description | Example |
|---|---|---|
| `CHUNKER_URL` | Chunker service URL | `http://localhost:8001` |
| `EMBED_URL` | Embed service URL | `http://localhost:8002` |
| `STORE_URL` | Store service URL | `http://localhost:8003` |
| `SEARCH_URL` | Search service URL | `http://localhost:8004` |
| `OLLAMA_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `llama3.1:8b` |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `legal_db` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | `yourpassword` |

---

## License

MIT