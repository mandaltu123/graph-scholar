## ScholarGraph-RAG

ScholarGraph-RAG is a local-first, LangGraph-powered agentic research paper chatbot. It ingests PDFs with LandingAI OCR, chunks and embeds content into ChromaDB, and answers questions with grounded citations using a local Llama server.

### Architecture (ASCII)

```
PDF Upload -> LandingAI OCR -> Chunking -> Embeddings -> ChromaDB
                                      \-> LangGraph (classify -> retrieve -> generate -> verify -> refine)
Client Chat UI <---------------------------------------------- Answer + Sources + Related Qs
```

### Backend Setup

```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8002
```

### Frontend Setup

```
cd frontend
npm install
npm run dev
```

### Environment Variables

- `LANDINGAI_API_KEY` / `LANDINGAI_ENDPOINT` / `LANDINGAI_MOCK`
- `LLAMA_BASE_URL` / `LLAMA_MODEL`
- `CHROMA_PERSIST_DIR`, `UPLOADS_DIR`, `EXTRACTED_DIR`

### Local Llama Options

- **Ollama (OpenAI-compatible endpoint)**  
  Start Ollama and use: `LLAMA_BASE_URL=http://localhost:11434/v1` and `LLAMA_MODEL=llama3.1`

- **llama.cpp server**  
  Run llama.cpp with the OpenAI-compatible server and set `LLAMA_BASE_URL=http://localhost:8001/v1`

### Usage

1. Upload a PDF from the UI.
2. Wait for indexing to complete.
3. Ask questions and review sources + related questions.

### Troubleshooting

- **OCR errors**: ensure LandingAI key and endpoint are correct, or set `LANDINGAI_MOCK=true`.
- **Llama endpoint errors**: verify local server is running and reachable at `LLAMA_BASE_URL`.
- **Chroma persistence**: ensure `storage/chroma` is writable.
