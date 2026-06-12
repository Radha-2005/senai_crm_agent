# SenAI CRM Agentic Intelligence Platform

A complete, production-grade, AI-powered CRM system capable of automated email ingestion, Layer 1 heuristics, Layer 2 LLM structured classifications, Layer 3 sentiment trend alerts, RAG policy grounding, Web Intelligence reputation scraping, and a multi-step autonomous ReAct agent loop.

---

## 🛠️ Tech Stack & Choices

- **FastAPI**: Asynchronous web frameworks handling ingestion streams, websockets, and REST client routing.
- **SQLAlchemy (Async)**: High-performance ORM mappings querying PostgreSQL.
- **ChromaDB & SentenceTransformers (`all-MiniLM-L6-v2`)**: Used for the RAG pipeline. Using `SentenceTransformers` allows local vector calculations at zero token costs. If configured, it can fall back to OpenAI's embedding API.
- **OpenAI GPT-4o-mini**: Drives structured Layer 2 classifications and drafts policy-compliant responses.
- **React + Bootstrap + Chart.js**: Desktop control room interface with real-time websocket pushes.

---

## 🏗️ System Architecture & Data Flow

1. **Ingest**: Email payloads hit `POST /api/ingest`. Validations block malformed JSONs. Idempotency is checked via message UUIDs.
2. **Layer 1 Heuristics**: Checks spam domain blocklists, urgencies, and internal routes in under 10ms.
3. **Layer 2 & 3 AI**: Non-spam messages trigger RAG lookups (retrieving top-3 policy chunks). The LLM classifies category, sentiment, and extracts entities. Sentiment is written to database snapshots; consecutive dropping values trigger alerts.
4. **Agent Loop**: If confidence is high (>0.70) and urgency is below Critical, the ReAct agent runs up to 6 tool calls to retrieve CRM profiles, scrape reviews, draft replies, or escalate.
5. **Human-in-the-Loop**: CSM agents review reasoning steps, modify proposed response drafts, and submit approvals.

---

## 📋 Environment Variables (`.env`)

Create a `.env` file at the root:
```ini
ENV=development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/senai_crm
GROQ_API_KEY=your_groq_api_key
LLM_MODEL=llama-3.3-70b-versatile
CHROMA_PERSIST_DIRECTORY=./chroma_db
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
SIMULATION_SPEED_DELAY=1.0
```

---

## 🚀 Getting Started

### 1. Seeding and Setup
Build the database tables and seed the knowledge base policies (both in Postgres and ChromaDB):
```bash
# Install package dependencies
pip install -r requirements.txt

# Run the seeding CLI
python scripts/seed_kb.py
```

### 2. Run the Backend API Server
Launch the FastAPI uvicorn daemon:
```bash
uvicorn backend.main:app --reload --port 8000
```

### 3. Run Ingestion Simulations
Simulate the incoming email stream from the dataset:
```bash
python scripts/replay_dataset.py --delay 1.0
```

### 4. Running Tests
Run the pytest suite:
```bash
pytest tests/
```

### 5. Running with Docker Compose
Start the database and API backend in a single command:
```bash
docker-compose up --build
```

---

## 🧠 Resolution of Conflicting Signals & Special Scenarios

- **Conflicting Sentiment**: When a client writes conflicting text (e.g. "I love the product but hate the billing"), the LLM yields a `Mixed` sentiment classification. Our agent loop automatically flags any classification confidence score below `0.70` for human review.
- **GDPR Request (msg_052)**: Caught by heuristic and legal filters. The agent calls `flag_for_legal()`, logs an internal compliance ticket (`create_internal_ticket()`), drafts a statutory response citing the 30-day compliance window, and escalates to human.
- **Ransomware Threat (msg_038)**: Flags as a critical security threat, registers an incident ticket, escalates immediately to the CISO queue, and **NEVER auto-replies** to the attacker.
- **Karen Refund Complaint (msg_033)**: Detects a drop in sentiment, scrapes Trustpilot/G2 reputation ratings, generates an CS brief with competitor rates, drafts a CS credit retention offer, and routes to CS specialists.
