import React, { useEffect, useMemo, useState } from "react";
import {
  chat,
  ChatResponse,
  DocStatusResponse,
  getDocStatus,
  uploadPdf,
} from "./api/client";
import ChatPanel, { ChatMessage } from "./components/ChatPanel";
import Sidebar from "./components/Sidebar";
import SourcesPanel from "./components/SourcesPanel";

export default function App() {
  const [docId, setDocId] = useState<string | null>(null);
  const [docStatus, setDocStatus] = useState<DocStatusResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const sessionId = useMemo(() => {
    const existing = localStorage.getItem("scholargraph_session_id");
    if (existing) return existing;
    const generated = crypto.randomUUID();
    localStorage.setItem("scholargraph_session_id", generated);
    return generated;
  }, []);

  const loadStatus = async (id: string) => {
    try {
      const data = await getDocStatus(id);
      setDocStatus(data);
    } catch (err) {
      setDocStatus(null);
      setError((err as Error).message);
    }
  };

  useEffect(() => {
    if (!docId) return;
    loadStatus(docId);
    const interval = setInterval(() => loadStatus(docId), 4000);
    return () => clearInterval(interval);
  }, [docId]);

  const handleUpload = async (file: File) => {
    setError("");
    setUploading(true);
    try {
      const response = await uploadPdf(file);
      setDocId(response.doc_id);
      await loadStatus(response.doc_id);
      setMessages([]);
      setLastResponse(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUploading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !docId) return;
    const userMessage: ChatMessage = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSending(true);
    try {
      const response = await chat({
        doc_id: docId,
        session_id: sessionId,
        message: userMessage.content,
        top_k: 5,
      });
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        relatedQuestions: response.related_questions,
        verified: response.verified,
        verificationNotes: response.verification_notes,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setLastResponse(response);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900">
      <Sidebar
        docId={docId}
        docStatus={docStatus}
        onUpload={handleUpload}
        uploading={uploading}
        onSampleQuestion={(text) => setInput(text)}
      />
      <main className="flex flex-1 flex-col">
        <ChatPanel
          messages={messages}
          input={input}
          onInputChange={setInput}
          onSend={handleSend}
          sending={sending}
          disabled={!docId || docStatus?.status !== "Ready"}
        />
      </main>
      <SourcesPanel response={lastResponse} />
      {error && (
        <div className="absolute bottom-6 right-6 rounded-lg bg-red-600 px-4 py-2 text-sm text-white shadow-lg">
          {error}
        </div>
      )}
    </div>
  );
}
