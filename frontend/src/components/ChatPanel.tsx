import React, { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { SourceChunk } from "../api/client";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  relatedQuestions?: string[];
  verified?: boolean;
  verificationNotes?: string;
}

interface ChatPanelProps {
  messages: ChatMessage[];
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  sending: boolean;
  disabled: boolean;
}

export default function ChatPanel({
  messages,
  input,
  onInputChange,
  onSend,
  sending,
  disabled,
}: ChatPanelProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  return (
    <section className="flex flex-1 flex-col">
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-200 bg-white px-6 py-8 text-sm text-slate-500">
            Upload a paper, wait for indexing, and ask your first question.
          </div>
        )}
        <div className="space-y-4">
          {messages.map((message, index) => (
            <div key={`${message.role}-${index}`} className="space-y-2">
              <div
                className={`max-w-2xl rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                  message.role === "user"
                    ? "ml-auto bg-slate-900 text-white"
                    : "bg-white text-slate-800"
                }`}
              >
                {message.role === "assistant" ? (
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                ) : (
                  message.content
                )}
              </div>
              {message.role === "assistant" && (
                <div className="max-w-2xl text-xs text-slate-500">
                  {message.verified ? "Verified" : "Needs verification"}
                  {message.verificationNotes && (
                    <span className="ml-2 text-slate-400">
                      {message.verificationNotes}
                    </span>
                  )}
                </div>
              )}
              {message.role === "assistant" &&
                message.relatedQuestions &&
                message.relatedQuestions.length > 0 && (
                  <div className="flex max-w-2xl flex-wrap gap-2 text-xs">
                    {message.relatedQuestions.map((question) => (
                      <button
                        key={question}
                        onClick={() => onInputChange(question)}
                        className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-slate-600 hover:bg-slate-100"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                )}
            </div>
          ))}
          {sending && (
            <div className="max-w-md rounded-2xl bg-white px-4 py-3 text-sm text-slate-400 shadow-sm">
              Thinking...
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>
      <div className="border-t border-slate-200 bg-white px-6 py-4">
        <textarea
          rows={3}
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          disabled={disabled}
          className="w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 disabled:bg-slate-100"
          placeholder={
            disabled
              ? "Upload and index a document to start chatting."
              : "Ask a question about the paper..."
          }
        />
        <div className="mt-3 flex justify-end">
          <button
            onClick={onSend}
            disabled={sending || !input.trim() || disabled}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            Send
          </button>
        </div>
      </div>
    </section>
  );
}
