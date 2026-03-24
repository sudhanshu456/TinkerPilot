'use client';

import { useEffect, useState } from 'react';

export default function SettingsPage() {
  const [docs, setDocs] = useState<any[]>([]);
  const [ingestPath, setIngestPath] = useState('');
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState('');
  const [health, setHealth] = useState<string>('checking...');

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then(() => setHealth('connected'))
      .catch(() => setHealth('not connected'));

    fetch('/api/documents')
      .then((r) => r.json())
      .then((data) => setDocs(data.documents || []))
      .catch(() => {});
  }, []);

  const pollJob = async (jobId: string) => {
    const poll = async (): Promise<void> => {
      try {
        const res = await fetch(`/api/documents/ingest/${jobId}`);
        const job = await res.json();
        if (job.status === 'done') {
          setIngestResult(`Ingested ${job.total_files} files, ${job.total_chunks} chunks`);
          setIngesting(false);
          const docsRes = await fetch('/api/documents');
          const docsData = await docsRes.json();
          setDocs(docsData.documents || []);
        } else if (job.status === 'error') {
          setIngestResult(`Error: ${job.error}`);
          setIngesting(false);
        } else {
          setTimeout(poll, 1000);
        }
      } catch {
        setIngestResult('Error: lost connection to server');
        setIngesting(false);
      }
    };
    poll();
  };

  const handleIngest = async () => {
    if (!ingestPath.trim()) return;
    setIngesting(true);
    setIngestResult('Ingesting in background...');
    try {
      const res = await fetch('/api/documents/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: ingestPath, recursive: true }),
      });
      const data = await res.json();
      if (data.status === 'accepted') {
        pollJob(data.job_id);
      } else {
        setIngestResult(`Error: ${data.detail || 'Unknown error'}`);
        setIngesting(false);
      }
    } catch (e: any) {
      setIngestResult(`Error: ${e.message}`);
      setIngesting(false);
    }
  };

  const handleDelete = async (id: number) => {
    await fetch(`/api/documents/${id}`, { method: 'DELETE' });
    setDocs(docs.filter((d) => d.id !== id));
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIngesting(true);
    setIngestResult(`Uploading ${file.name}...`);
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch('/api/documents/upload', { method: 'POST', body: form });
      const data = await res.json();
      if (data.status === 'accepted') {
        setIngestResult(`Indexing ${data.filename} in background...`);
        pollJob(data.job_id);
      } else {
        setIngestResult(`Error: ${data.detail || 'Unknown error'}`);
        setIngesting(false);
      }
    } catch (e: any) {
      setIngestResult(`Error: ${e.message}`);
      setIngesting(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1.5rem' }}>Settings</h1>

      {/* Status */}
      <Section title="System Status">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{
            width: '8px', height: '8px', borderRadius: '50%',
            background: health === 'connected' ? 'var(--success)' : 'var(--danger)',
            display: 'inline-block',
          }} />
          <span>Backend: {health}</span>
        </div>
      </Section>

      {/* Document Management */}
      <Section title="Knowledge Base">
        <div style={{ marginBottom: '1rem' }}>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            Ingest files or directories to add them to the searchable knowledge base.
          </p>

          {/* Path ingest */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <input
              value={ingestPath}
              onChange={(e) => setIngestPath(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleIngest()}
              placeholder="Local path: ~/Documents/project or /path/to/file.pdf"
              style={{
                flex: 1, background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
                color: 'var(--text-primary)', borderRadius: '6px', padding: '0.5rem 0.75rem',
                fontSize: '0.85rem', outline: 'none',
              }}
            />
            <button onClick={handleIngest} disabled={ingesting} style={{
              background: 'var(--accent)', color: 'white', border: 'none',
              borderRadius: '6px', padding: '0.5rem 1rem', cursor: 'pointer',
              fontWeight: 600, fontSize: '0.85rem', opacity: ingesting ? 0.6 : 1,
            }}>
              {ingesting ? 'Ingesting...' : 'Ingest'}
            </button>
          </div>

          {/* File upload */}
          <label style={{
            display: 'inline-block', padding: '0.5rem 1rem',
            background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
            borderRadius: '6px', cursor: 'pointer', fontSize: '0.85rem',
            color: 'var(--text-secondary)',
          }}>
            Upload file
            <input type="file" onChange={handleUpload} hidden />
          </label>

          {ingestResult && (
            <div style={{
              marginTop: '0.75rem', fontSize: '0.85rem',
              color: ingestResult.startsWith('Error') ? 'var(--danger)' : 'var(--success)',
            }}>
              {ingestResult}
            </div>
          )}
        </div>

        {/* Document list */}
        <div>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            Indexed Documents ({docs.length})
          </h4>
          {docs.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              No documents indexed yet.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', maxHeight: '400px', overflowY: 'auto' }}>
              {docs.map((doc) => (
                <div key={doc.id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  background: 'var(--bg-tertiary)', padding: '0.5rem 0.75rem',
                  borderRadius: '6px', fontSize: '0.85rem',
                }}>
                  <div>
                    <span style={{ fontWeight: 500 }}>{doc.filename}</span>
                    <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem', fontSize: '0.75rem' }}>
                      {doc.chunk_count} chunks | {formatSize(doc.file_size)} | {doc.file_type}
                    </span>
                  </div>
                  <button onClick={() => handleDelete(doc.id)} style={{
                    background: 'transparent', border: 'none', color: 'var(--danger)',
                    cursor: 'pointer', fontSize: '0.8rem',
                  }}>
                    remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </Section>

      {/* Model Info */}
      <Section title="AI Models">
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          <p><strong>LLM:</strong> Qwen2.5-3B-Instruct via Ollama (Metal GPU)</p>
          <p><strong>Embeddings:</strong> Qwen3-Embedding 0.6B via Ollama (Metal GPU)</p>
          <p><strong>Speech-to-Text:</strong> Moonshine Voice (streaming, 73ms latency)</p>
          <p><strong>Text-to-Speech:</strong> Kokoro-82M (6 voices, faster-than-realtime)</p>
          <p style={{ marginTop: '0.5rem' }}>All models run locally with Metal GPU acceleration. No cloud APIs used.</p>
        </div>
      </Section>

      {/* CLI reference */}
      <Section title="CLI Quick Reference">
        <div style={{ fontSize: '0.85rem', fontFamily: 'monospace', lineHeight: 1.8 }}>
          <p><code style={codeBg}>tp ask &quot;how does auth work?&quot;</code> - Ask with RAG</p>
          <p><code style={codeBg}>tp ingest ~/project</code> - Index a directory</p>
          <p><code style={codeBg}>tp search &quot;database migration&quot;</code> - Semantic search</p>
          <p><code style={codeBg}>tp transcribe meeting.wav</code> - Transcribe audio</p>
          <p><code style={codeBg}>tp tasks</code> - List tasks</p>
          <p><code style={codeBg}>tp explain script.py</code> - Explain a file</p>
          <p><code style={codeBg}>tp convert data.csv --to json</code> - Convert files</p>
          <p><code style={codeBg}>tp cmd &quot;find large files&quot;</code> - NL to shell cmd</p>
          <p><code style={codeBg}>tp git-digest /path/to/repo</code> - Summarize git</p>
          <p><code style={codeBg}>tp listen</code> - Speech-to-text</p>
          <p><code style={codeBg}>tp speak &quot;hello&quot;</code> - Text-to-speech</p>
          <p><code style={codeBg}>tp voices</code> - List TTS voices</p>
          <p><code style={codeBg}>tp digest</code> - Daily briefing</p>
          <p><code style={codeBg}>tp serve</code> - Start backend server</p>
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{
      background: 'var(--bg-secondary)', border: '1px solid var(--border)',
      borderRadius: '8px', padding: '1.25rem', marginBottom: '1rem',
    }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--accent)' }}>{title}</h3>
      {children}
    </div>
  );
}

const codeBg: React.CSSProperties = {
  background: 'var(--bg-tertiary)',
  padding: '0.15rem 0.4rem',
  borderRadius: '4px',
};
