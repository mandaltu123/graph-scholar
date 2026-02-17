export interface UploadResponse {
  doc_id: string;
  filename: string;
  status: string;
}

export interface DocStatusResponse {
  doc_id: string;
  filename: string;
  status: string;
  chunk_count: number;
  embedded: boolean;
  created_at: string;
  updated_at: string;
  embedding_model?: string | null;
  error?: string | null;
}

export interface ChatRequest {
  doc_id: string;
  session_id: string;
  message: string;
  top_k: number;
}

export interface SourceChunk {
  chunk_id: string;
  text: string;
  page_num?: number | null;
  score: number;
  metadata: Record<string, unknown>;
}

export interface ChatResponse {
  answer: string;
  sources: SourceChunk[];
  related_questions: string[];
  verified: boolean;
  verification_notes: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Request failed");
  }
  return (await res.json()) as T;
}

export async function uploadPdf(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE_URL}/api/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Upload failed");
  }
  return (await res.json()) as UploadResponse;
}

export async function getDocStatus(docId: string): Promise<DocStatusResponse> {
  return request(`/api/docs/${docId}/status`);
}

export async function chat(body: ChatRequest): Promise<ChatResponse> {
  return request("/api/chat", { method: "POST", body: JSON.stringify(body) });
}
