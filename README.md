# GraphScholar RAG

**Upload research papers (PDF) and chat with them using a LangGraph-powered RAG pipeline.** Supports multi-turn conversation with session memory, answer verification, and OCR for scanned documents.

## What It Does

- Upload PDF research papers via REST API
- Chunks text using configurable strategies (semantic/fixed-size)
- Embeds and stores chunks in ChromaDB
- Handles queries via a LangGraph state graph: retrieve → classify → generate → verify
- Verifies answers against retrieved chunks with heuristic grounding
- Suggests related questions after each answer
- Session-aware chat history for multi-turn conversations
- OCR support for scanned PDFs via LandingAI

## RAG Graph Flow

```
User question
      │
      ▼
 Classify (needs retrieval?)
      │
   ┌──┴──┐
   yes   no (use history)
   │
   ▼
ChromaDB retrieval (top-k chunks)
      │
      ▼
 Generate answer (OpenAI GPT)
      │
      ▼
 Verify + ground check
      │
   ┌──┴──┐
 pass  fail (retry, max 2)
   │
   ▼
 Related questions → Final response
```

## Quick Start

```bash
cd GraphScholar-RAG/backend
pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload
# API docs at http://localhost:8000/docs
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/upload` | Upload a PDF for ingestion |
| POST | `/chat` | Ask a question about an ingested document |
| GET | `/docs` | List all ingested documents |
| GET | `/health` | Health check |

## Tech Stack

- **Orchestration**: LangGraph (StateGraph with conditional edges)
- **Embedding**: OpenAI `text-embedding-3-small`
- **Generation**: OpenAI GPT-4o-mini
- **Vector Store**: ChromaDB
- **OCR**: LandingAI (for scanned PDFs)
- **API**: FastAPI + Uvicorn

## Project Structure

```
GraphScholar-RAG/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/           # Routes: upload, chat, docs, health
│   │   ├── services/
│   │   │   ├── rag_graph.py    # LangGraph RAG pipeline
│   │   │   ├── vectorstore.py  # ChromaDB operations
│   │   │   ├── embeddings.py   # OpenAI embeddings
│   │   │   ├── chunking.py     # Text chunking strategies
│   │   │   ├── ingest.py       # PDF ingestion pipeline
│   │   │   ├── verifier.py     # Answer grounding check
│   │   │   └── ocr_landingai.py # OCR for scanned PDFs
│   │   └── core/config.py
│   ├── tests/
│   └── requirements.txt
└── README.md
```
