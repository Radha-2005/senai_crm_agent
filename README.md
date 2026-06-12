# SenAI CRM — Agentic Intelligence Platform

## Overview
SenAI is a production-grade, AI-powered CRM platform that autonomously triages customer emails using a **ReAct (Reason + Act)** agent loop, multi-layer classification, RAG-powered policy retrieval, and real-time analytics.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  Frontend (React + Vite)  :5173                      │
│  Pages: Inbox, Thread Workspace, Analytics, Agent   │
└─────────────────────────┬────────────────────────────┘
                          │ HTTP/API Proxy
┌─────────────────────────▼────────────────────────────┐
│  FastAPI Backend  :8000                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │  Ingestion  │  │  Triage API  │  │  Analytics  │  │
│  │  Pipeline   │  │  Agent Loop  │  │  Dashboard  │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘  │
│         │                │                  │         │
│  ┌──────▼──────────────────────────────────▼──────┐  │
│  │              Agent Services                     │  │
│  │  Heuristic → LLM Classifier → ReAct Agent      │  │
│  │  RAG (ChromaDB + SentenceTransformers)          │  │
│  │  Web Intelligence (Reputation Scraping)         │  │
│  └─────────────────────────┬────────────────────── ┘  │
│                            │                          │
│  ┌─────────────────────────▼────────────────────────┐ │
│  │  PostgreSQL :5432  │  ChromaDB (local)            │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL 14+ (installed locally, default port 5432)

### 1. Create Virtual Environment
```bash
python -m venv senaienv
# Windows:
senaienv\Scripts\activate
# Linux/Mac:
source senaienv/bin/activate
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Edit `.env` with your settings:
```bash
# Required: Set your PostgreSQL password
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/postgres

# Required: Set Groq API key (get free key at https://console.groq.com)
GROQ_API_KEY=gsk_your_key_here
```

### 4. Seed Knowledge Base
```bash
python scripts/seed_kb.py
```

### 5. Run Backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 6. Run Frontend
```bash
cd frontend
npm install
npm run dev
```

### 7. Load Email Dataset
```bash
python scripts/replay_dataset.py
```

### 8. Access the App
- **Frontend Dashboard**: http://localhost:5173
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/api/v1/health

## Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_agent.py -v
pytest tests/test_api.py -v
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Autonomous Agent** | ReAct loop with 6 tool functions (policy search, ticket creation, legal flagging) |
| **Multi-layer Classification** | Heuristic rules → LLM (Groq llama-3.3-70b) with confidence gating |
| **RAG Pipeline** | ChromaDB + SentenceTransformers for policy document retrieval |
| **Sentiment Analysis** | Rule-based sentiment with trend deterioration detection |
| **Web Intelligence** | Company reputation scraping with TTL caching |
| **Draft Approval** | Human-in-the-loop review and approval of AI-generated replies |
| **GDPR Compliance** | Automatic data subject request detection and legal flagging |

## The 6 Evaluation Scenarios

| Scenario | Expected Decision |
|----------|-----------------|
| GDPR Data Portability Request | `Legal-Flag` |
| Ransomware Threat | `Legal-Flag` |
| Karen Refund + Legal Threat | `Escalate` |
| Chatbot Misinformation | `Escalate` |
| Bob SLA Breach + Legal | `Legal-Flag` |
| Alice Pricing Upgrade | `Auto-Reply` |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/ingest` | Ingest a new email |
| GET | `/api/v1/threads` | List threads |
| GET | `/api/v1/threads/{id}` | Get thread details |
| GET | `/api/v1/emails/{id}` | Get email details |
| PATCH | `/api/v1/emails/{id}/draft` | Edit draft reply |
| POST | `/api/v1/emails/{id}/approve` | Approve draft |
| GET | `/api/v1/analytics/dashboard` | Dashboard stats |
| GET | `/api/v1/agent/dry-run` | Run all 6 scenarios |
| POST | `/api/v1/agent/triage/manual` | Manual triage |
| POST | `/api/v1/rag/search` | Search knowledge base |
| GET | `/api/v1/health` | Health check |

## Docker Deployment
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend
```
