const API_BASE = '/api';

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// Chat
export const chatSend = (message: string, useRag = true, sessionId = 'default') =>
  apiFetch<{ answer: string; sources: any[]; session_id: string }>('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, use_rag: useRag, session_id: sessionId }),
  });

export const getChatHistory = (sessionId = 'default') =>
  apiFetch<any[]>(`/chat/history?session_id=${sessionId}`);

export const clearChatHistory = (sessionId = 'default') =>
  apiFetch<any>(`/chat/history?session_id=${sessionId}`, { method: 'DELETE' });

// Documents
export const getDocuments = () =>
  apiFetch<{ documents: any[]; total: number }>('/documents');

export const ingestPath = (path: string, recursive = true) =>
  apiFetch<any>('/documents/ingest', {
    method: 'POST',
    body: JSON.stringify({ path, recursive }),
  });

export const deleteDocument = (id: number) =>
  apiFetch<any>(`/documents/${id}`, { method: 'DELETE' });

export const uploadDocument = async (file: File) => {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/documents/upload`, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
};

// Meetings
export const getMeetings = () =>
  apiFetch<{ meetings: any[] }>('/meetings');

export const getMeeting = (id: number) =>
  apiFetch<any>(`/meetings/${id}`);

export const uploadAudioForTranscription = async (file: File, title?: string) => {
  const form = new FormData();
  form.append('file', file);
  if (title) form.append('title', title);
  const res = await fetch(`${API_BASE}/meetings/transcribe`, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Transcription failed');
  return res.json();
};

export const deleteMeeting = (id: number) =>
  apiFetch<any>(`/meetings/${id}`, { method: 'DELETE' });

// Tasks
export const getTasks = (status?: string) =>
  apiFetch<{ tasks: any[]; total: number }>(`/tasks${status ? `?status=${status}` : ''}`);

export const createTask = (title: string, priority = 'medium', dueDate?: string) =>
  apiFetch<any>('/tasks', {
    method: 'POST',
    body: JSON.stringify({ title, priority, due_date: dueDate }),
  });

export const updateTask = (id: number, data: any) =>
  apiFetch<any>(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) });

export const deleteTask = (id: number) =>
  apiFetch<any>(`/tasks/${id}`, { method: 'DELETE' });

// Digest
export const getDigest = () =>
  apiFetch<{ digest: string; raw: any }>('/digest');

// Search
export const search = (query: string, limit = 10) =>
  apiFetch<{ query: string; results: any }>(`/search?q=${encodeURIComponent(query)}&limit=${limit}`);

// Utils
export const explainCode = (content: string, filename?: string) =>
  apiFetch<{ explanation: string }>('/utils/explain', {
    method: 'POST',
    body: JSON.stringify({ content, filename }),
  });

export const analyzeLog = (content: string, filename?: string) =>
  apiFetch<{ analysis: string }>('/utils/analyze-log', {
    method: 'POST',
    body: JSON.stringify({ content, filename }),
  });

export const suggestCommand = (description: string) =>
  apiFetch<{ command: string }>('/utils/cmd', {
    method: 'POST',
    body: JSON.stringify({ description }),
  });

export const gitDigest = (repoPath: string, numCommits = 20) =>
  apiFetch<{ digest: string }>('/utils/git-digest', {
    method: 'POST',
    body: JSON.stringify({ repo_path: repoPath, num_commits: numCommits }),
  });

// Health
export const healthCheck = () => apiFetch<{ status: string }>('/health');

// WebSocket chat helper
export function createChatWebSocket(
  onToken: (token: string) => void,
  onSources: (sources: any[]) => void,
  onDone: (fullResponse: string) => void,
  onError: (error: string) => void,
): WebSocket {
  const ws = new WebSocket(`ws://127.0.0.1:8000/ws/chat`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch (data.type) {
      case 'token':
        onToken(data.content);
        break;
      case 'sources':
        onSources(data.sources);
        break;
      case 'done':
        onDone(data.full_response);
        break;
      case 'error':
        onError(data.error);
        break;
    }
  };

  ws.onerror = () => onError('WebSocket connection error');
  return ws;
}
