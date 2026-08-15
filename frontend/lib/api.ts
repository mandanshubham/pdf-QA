// frontend/lib/api.ts
// Typed API client — all backend calls go through here.

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Types ──────────────────────────────────────────────────────────────────

export interface DocumentInfo {
  doc_id: string;
  filename: string;
  chunk_count: number;
  upload_timestamp: string;
  file_size_bytes: number;
}

export interface SourceCitation {
  filename: string;
  page: number;
  score: number;
  snippet: string;
  doc_id: string;
}

export interface ChatResponse {
  question: string;
  answer: string;
  sources: SourceCitation[];
  chunks_searched: number;
}

export interface StreamEvent {
  type: 'token' | 'sources' | 'done' | 'error';
  content?: string;
  sources?: SourceCitation[];
  error?: string;
}

export interface UploadResponse {
  message: string;
  doc_id: string;
  filename: string;
  chunk_count: number;
}

// ── Documents API ──────────────────────────────────────────────────────────

export async function listDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_BASE}/api/documents`);
  if (!res.ok) throw new Error('Failed to list documents');
  const data = await res.json();
  return data.documents;
}

export async function uploadDocuments(files: File[]): Promise<UploadResponse[]> {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/documents/${docId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete document');
}

// ── Chat API ───────────────────────────────────────────────────────────────

export async function askQuestion(
  question: string,
  docIds?: string[]
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, doc_ids: docIds }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Chat failed' }));
    throw new Error(err.detail || 'Chat failed');
  }
  return res.json();
}

/**
 * Stream a chat response using SSE.
 * Calls onToken for each token, onSources when citations arrive, onDone when finished.
 */
export async function streamQuestion(
  question: string,
  onToken: (token: string) => void,
  onSources: (sources: SourceCitation[]) => void,
  onDone: () => void,
  onError: (error: string) => void,
  docIds?: string[]
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, doc_ids: docIds }),
  });

  if (!res.ok || !res.body) {
    onError('Failed to connect to stream');
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const json = line.slice(6).trim();
      if (!json) continue;

      try {
        const event: StreamEvent = JSON.parse(json);
        if (event.type === 'token' && event.content) {
          onToken(event.content);
        } else if (event.type === 'sources' && event.sources) {
          onSources(event.sources);
        } else if (event.type === 'done') {
          onDone();
        } else if (event.type === 'error') {
          onError(event.error || 'Unknown error');
        }
      } catch {
        // ignore malformed events
      }
    }
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}
