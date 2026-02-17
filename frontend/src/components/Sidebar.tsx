import React from "react";
import { DocStatusResponse } from "../api/client";

const SAMPLE_QUESTIONS = [
  "What problem does the paper address?",
  "Summarize the main contributions.",
  "What datasets were used?",
  "Describe the methodology in brief.",
  "What are the key results?",
];

interface SidebarProps {
  docId: string | null;
  docStatus: DocStatusResponse | null;
  onUpload: (file: File) => void;
  uploading: boolean;
  onSampleQuestion: (text: string) => void;
}

export default function Sidebar({
  docId,
  docStatus,
  onUpload,
  uploading,
  onSampleQuestion,
}: SidebarProps) {
  return (
    <aside className="flex h-full w-80 flex-col border-r border-slate-200 bg-white p-4">
      <div className="mb-6">
        <h1 className="text-lg font-semibold">ScholarGraph-RAG</h1>
        <p className="text-xs text-slate-500">
          Agentic research paper chatbot with local Llama.
        </p>
      </div>

      <label className="mb-4 inline-flex cursor-pointer items-center justify-center rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">
        <input
          type="file"
          accept="application/pdf"
          className="hidden"
          disabled={uploading}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onUpload(file);
          }}
        />
        {uploading ? "Uploading..." : "Upload PDF"}
      </label>

      <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
        <div className="font-semibold text-slate-700">Document Status</div>
        <div className="mt-2 space-y-1">
          <div>Doc ID: {docId ?? "None"}</div>
          <div>Status: {docStatus?.status ?? "Idle"}</div>
          <div>Chunks: {docStatus?.chunk_count ?? 0}</div>
          <div>Embedded: {docStatus?.embedded ? "Yes" : "No"}</div>
        </div>
        {docStatus?.error && (
          <div className="mt-2 text-red-600">{docStatus.error}</div>
        )}
      </div>

      <div className="mt-6 text-xs uppercase tracking-wide text-slate-400">
        Sample Questions
      </div>
      <div className="mt-3 flex flex-col gap-2 text-xs">
        {SAMPLE_QUESTIONS.map((question) => (
          <button
            key={question}
            onClick={() => onSampleQuestion(question)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-slate-600 hover:bg-slate-50"
          >
            {question}
          </button>
        ))}
      </div>
    </aside>
  );
}
