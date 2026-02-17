import json

from app.services import rag_graph


class DummyClient:
    def __init__(self):
        self.calls = 0

    def chat(self, messages, temperature=None, max_tokens=None):
        self.calls += 1
        if "classifier" in messages[0]["content"].lower():
            return "RETRIEVE"
        if "related questions" in messages[0]["content"].lower():
            return json.dumps(["Q1", "Q2", "Q3"])
        return "Answer with citation [p1-c0]"


def test_rag_graph_retry(monkeypatch):
    dummy = DummyClient()
    monkeypatch.setattr(rag_graph, "get_llm_client", lambda: dummy)
    monkeypatch.setattr(
        rag_graph,
        "query_chunks",
        lambda embedding, top_k, doc_id: {
            "ids": [["doc-1:p1-c0"]],
            "documents": [["Chunk text"]],
            "metadatas": [[{"doc_id": doc_id, "page_num": 1, "chunk_ref": "p1-c0"}]],
            "distances": [[0.1]],
        },
    )
    monkeypatch.setattr(
        rag_graph,
        "verify_answer",
        lambda answer, context: {
            "grounded": True,
            "unsupported_claims": [],
            "fix_suggestion": "",
        },
    )
    monkeypatch.setattr(
        rag_graph,
        "heuristic_grounding",
        lambda answer, chunk_ids: {"ok": True, "notes": ""},
    )
    state = rag_graph.run_graph(
        doc_id="doc-1",
        session_id="s1",
        question="What is this about?",
        chat_history=[],
    )
    assert state["final_answer"]
    assert state["related_questions"]
