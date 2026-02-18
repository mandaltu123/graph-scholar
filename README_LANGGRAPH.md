# LangGraph System Guide

This document explains how the LangGraph workflow in this project operates, the core concepts it uses, and common interview questions to evaluate understanding.

## What the LangGraph Does

The application uses a LangGraph state machine to orchestrate a controlled Retrieval-Augmented Generation (RAG) flow. It takes a user question, retrieves relevant chunks from a vector store, generates a grounded answer with citations, verifies that answer, and optionally retries with stricter constraints if verification fails.

## LangGraph Framework Used

This project uses the **LangGraph (Python)** framework from the `langgraph` package. The workflow is implemented with a `StateGraph` that defines nodes, edges, and conditional transitions.

## High-Level Flow

```
entry
  -> classify_query
  -> retrieve
  -> generate
  -> verify
  -> (verified) -> related_qs -> end
  -> (not verified & retries left) -> refine -> verify
  -> (retries exceeded) -> final fallback
```

## Core State Fields

- `doc_id`: The document to query.
- `session_id`: Chat session identifier (memory scope).
- `question`: The user query.
- `chat_history`: Recent message context.
- `retrieved_chunks`: Top-k retrieved passages.
- `draft_answer`: Candidate response from LLM.
- `verified`: Whether the answer is grounded.
- `retries`: Current retry count.
- `final_answer`: Answer returned to the user.
- `related_questions`: Follow-up questions.
- `verification_notes`: Reasons for rejection or fixes.

## Key Nodes and Responsibilities

### 1) classify_query
Determines whether retrieval is needed. For document-specific questions, retrieval is enabled. For app usage/help questions, retrieval is skipped.

### 2) retrieve
Embeds the query and performs a top-k similarity search in Chroma. The output is the `retrieved_chunks` array with text and metadata.

### 3) generate
Uses a strict system prompt that enforces citation formats (e.g., `[p3-c12]`) and a “use context only” constraint. The response is stored as `draft_answer`.

### 4) verify
Runs a verifier LLM to check grounding and also applies heuristic checks:
- Must include at least one citation
- All cited chunk IDs must exist in `retrieved_chunks`

### 5) refine
If verification fails and retries remain, the system regenerates with stronger constraints and verifier feedback.

### 6) related_qs
Generates 3–5 related questions based on the retrieved context.

## Grounding and Safety

Grounding is enforced in two layers:
1) **LLM verifier** returns structured JSON describing whether the answer is supported.
2) **Heuristic checks** ensure citations exist and are valid.

If grounding fails after the retry limit, the system returns a safe fallback message rather than hallucinating.

## Session Memory

Session memory is lightweight and scoped per `session_id`. A short list of recent messages is stored and injected into the `generate` prompt to preserve conversational context without exploding token usage.

## Why LangGraph (vs. Simple Chains)

LangGraph is used because:
- It provides explicit control flow and branching (verify, retry).
- It supports stateful workflows with retries.
- It allows deterministic, auditable decisions in RAG pipelines.

## Common Failure Modes

- **No chunks retrieved**: Wrong `doc_id`, empty OCR output, or vector store mismatch.
- **No citations**: LLM did not follow the prompt; verifier will reject.
- **Incorrect endpoint**: Llama or OCR endpoints unreachable.

## Tuning Recommendations

- Increase `top_k` if answers miss relevant context.
- Increase `chunk_size` or overlap if semantic continuity is lost.
- Adjust retry limit if verification is too strict.

## Interview Questions

### Conceptual
1) Why is a state machine useful for RAG workflows?  
**Answer:** It makes control flow explicit and testable (retrieve → generate → verify → retry). You can branch on verification outcomes and keep state across steps, which is harder to express in a linear chain.

2) What are the trade-offs of LLM-based verification vs. heuristic verification?  
**Answer:** LLM verification is flexible and can reason about nuanced grounding, but it adds latency/cost and can be inconsistent. Heuristics are fast and deterministic but can be overly strict or miss subtle unsupported claims. Combining both gives balance.

3) How does chunk size affect retrieval quality and latency?  
**Answer:** Larger chunks improve context continuity but reduce retrieval precision and increase prompt size/latency. Smaller chunks improve recall/precision but can lose context, requiring more chunks and potentially more tokens.

### System Design
1) How would you handle long documents without exceeding context limits?  
**Answer:** Use smaller chunks with overlap, retrieve top‑k, and add a re-ranking stage. Summarize sections or use hierarchical retrieval (section → chunk). Apply context window truncation and prioritize by relevance score.

2) How would you add async ingestion and progress updates?  
**Answer:** Move OCR + embedding to a background task queue (Celery, RQ, or FastAPI background worker). Store ingestion status in a DB and expose polling or WebSocket/SSE progress updates to the UI.

3) How would you support multi-document retrieval?  
**Answer:** Store all chunks in a single collection with `doc_id` metadata and query with filters or re-rank across documents. Update prompts to list sources with doc IDs and return grouped citations.

### Debugging
1) What steps would you take if retrieval returns no chunks?  
**Answer:** Verify doc_id matches indexed data, confirm OCR output exists, check embedding model load, and ensure Chroma persisted data. Query the vector store directly to inspect documents.

2) How would you validate that OCR output is correct?  
**Answer:** Persist raw OCR responses, inspect extracted text files, and validate page counts/sections. Compare sampled OCR text with the original PDF.

3) How would you detect and prevent hallucinations?  
**Answer:** Enforce citations per sentence, run a verifier step, and fall back to “not in context” when grounding fails. Add heuristic checks for citation IDs.

### Practical Coding
1) How would you implement a more robust citation validator?  
**Answer:** Parse citations with regex, verify each cited ID exists in retrieved chunks, and ensure every sentence includes at least one citation. Reject or rewrite answers that fail.

2) How would you extend the graph with a summarization node?  
**Answer:** Add a `summarize` node after retrieval that compresses top‑k chunks, then feed the summary into `generate`. Keep the original chunks for citations.

3) How would you cache embeddings to speed ingestion?  
**Answer:** Hash chunk text and store embeddings in a cache (disk or DB). On re‑ingestion, reuse cached vectors if the hash matches to avoid recomputation.

## Quick Diagram of Data Flow

```
PDF -> OCR -> Chunk -> Embed -> Chroma
                     |
User -> LangGraph -> Retrieve -> Generate -> Verify -> Answer
```

---

If you want a more detailed, file-by-file walkthrough, tell me and I can expand this guide with exact module references and code excerpts.
