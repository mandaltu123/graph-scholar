import React from "react";
import { ChatResponse } from "../api/client";

interface SourcesPanelProps {
  response: ChatResponse | null;
}

export default function SourcesPanel({ response }: SourcesPanelProps) {
  const sources = response?.sources ?? [];
  return (
    <aside className="flex h-full w-80 flex-col border-l border-slate-200 bg-white p-4">
      <div className="mb-4 text-xs uppercase tracking-wide text-slate-400">
        Sources
      </div>
      <div className="space-y-3 overflow-y-auto">
        {sources.length === 0 && (
          <div className="text-sm text-slate-500">
            No sources available yet.
          </div>
        )}
        {sources.map((source, index) => (
          <details
            key={`${source.chunk_id}-${index}`}
            className="rounded-lg border border-slate-200 p-3 text-xs"
          >
            <summary className="cursor-pointer font-medium text-slate-700">
              {source.chunk_id}
              {source.page_num !== undefined && (
                <span className="ml-2 text-slate-400">p.{source.page_num}</span>
              )}
            </summary>
            <div className="mt-2 text-slate-600">{source.text}</div>
          </details>
        ))}
      </div>
    </aside>
  );
}
