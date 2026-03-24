'use client';

import { useState } from 'react';

interface DocChunk {
  text: string;
  filename: string;
  filepath: string;
  file_type: string;
  relevance: number;
  line_start?: number;
}

interface GroupedDoc {
  filename: string;
  filepath: string;
  file_type: string;
  bestRelevance: number;
  chunks: DocChunk[];
}

function groupDocuments(docs: DocChunk[]): GroupedDoc[] {
  const map = new Map<string, GroupedDoc>();
  for (const doc of docs) {
    const key = doc.filepath || doc.filename;
    if (!map.has(key)) {
      map.set(key, {
        filename: doc.filename,
        filepath: doc.filepath,
        file_type: doc.file_type,
        bestRelevance: doc.relevance,
        chunks: [],
      });
    }
    const group = map.get(key)!;
    group.chunks.push(doc);
    if (doc.relevance > group.bestRelevance) group.bestRelevance = doc.relevance;
  }
  return Array.from(map.values()).sort((a, b) => b.bestRelevance - a.bestRelevance);
}

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  const doSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setExpandedDoc(null);
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=20`);
      const data = await res.json();
      setResults(data.results);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const grouped = results?.documents ? groupDocuments(results.documents) : [];
  const totalResults =
    grouped.length + (results?.tasks?.length || 0) + (results?.meetings?.length || 0);

  return (
    <div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>Search</h1>

      {/* Search bar */}
      <div style={{
        display: 'flex', gap: '0.5rem', marginBottom: '1.5rem',
        background: 'var(--bg-secondary)', border: '1px solid var(--border)',
        borderRadius: '8px', padding: '0.5rem',
      }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && doSearch()}
          placeholder="Search across docs, tasks, meetings, notes..."
          style={{
            flex: 1, background: 'transparent', border: 'none',
            color: 'var(--text-primary)', outline: 'none', padding: '0.5rem',
            fontSize: '0.95rem',
          }}
        />
        <button onClick={doSearch} disabled={loading} style={{
          background: 'var(--accent)', color: 'white', border: 'none',
          borderRadius: '6px', padding: '0.5rem 1.2rem', cursor: 'pointer',
          fontWeight: 600, fontSize: '0.9rem', opacity: loading ? 0.6 : 1,
        }}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <div style={{ color: 'var(--danger)', marginBottom: '1rem', fontSize: '0.85rem' }}>{error}</div>}

      {results && (
        <div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
            {totalResults} results for &quot;{query}&quot;
          </p>

          {/* Documents — grouped by file */}
          {grouped.length > 0 && (
            <ResultSection title="Documents" count={grouped.length}>
              {grouped.map((doc) => {
                const isExpanded = expandedDoc === (doc.filepath || doc.filename);
                return (
                  <div key={doc.filepath || doc.filename} style={resultCard}>
                    {/* Header row — clickable to expand */}
                    <div
                      onClick={() => setExpandedDoc(isExpanded ? null : (doc.filepath || doc.filename))}
                      style={{ cursor: 'pointer' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--accent)' }}>
                          {doc.filename}
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>
                            {doc.chunks.length} matching section{doc.chunks.length > 1 ? 's' : ''}
                          </span>
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                          relevance: {doc.bestRelevance}
                        </span>
                      </div>
                      {/* File path */}
                      {doc.filepath && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.4rem', fontFamily: 'monospace' }}>
                          {doc.filepath}
                        </div>
                      )}
                      {/* Preview of best chunk when collapsed */}
                      {!isExpanded && (
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                          {doc.chunks[0].text}
                        </p>
                      )}
                    </div>

                    {/* Expanded: show all chunks */}
                    {isExpanded && (
                      <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {doc.chunks.map((chunk, ci) => (
                          <div key={ci} style={{
                            background: 'var(--bg-tertiary)', borderRadius: '6px',
                            padding: '0.6rem 0.75rem', borderLeft: '3px solid var(--accent)',
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                {chunk.line_start ? `Line ${chunk.line_start}` : `Section ${ci + 1}`}
                              </span>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                relevance: {chunk.relevance}
                              </span>
                            </div>
                            <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap' }}>
                              {chunk.text}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </ResultSection>
          )}

          {/* Tasks */}
          {results.tasks?.length > 0 && (
            <ResultSection title="Tasks" count={results.tasks.length}>
              {results.tasks.map((task: any) => (
                <div key={task.id} style={resultCard}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{task.title}</span>
                    <span style={{
                      fontSize: '0.75rem', padding: '0.1rem 0.5rem', borderRadius: '10px',
                      background: task.status === 'done' ? 'var(--success)' : 'var(--bg-tertiary)',
                      color: task.status === 'done' ? 'white' : 'var(--text-secondary)',
                    }}>
                      {task.status}
                    </span>
                  </div>
                </div>
              ))}
            </ResultSection>
          )}

          {/* Meetings */}
          {results.meetings?.length > 0 && (
            <ResultSection title="Meetings" count={results.meetings.length}>
              {results.meetings.map((m: any) => (
                <div key={m.id} style={resultCard}>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.3rem' }}>{m.title}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.3rem' }}>{m.date?.slice(0, 10)}</div>
                  {m.snippet && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {m.snippet}
                    </p>
                  )}
                </div>
              ))}
            </ResultSection>
          )}

          {/* Notes */}
          {results.notes?.length > 0 && (
            <ResultSection title="Notes" count={results.notes.length}>
              {results.notes.map((n: any, i: number) => (
                <div key={i} style={resultCard}>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.3rem' }}>{n.title}</div>
                  {n.snippet && (
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {n.snippet}
                    </p>
                  )}
                </div>
              ))}
            </ResultSection>
          )}

          {totalResults === 0 && (
            <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
              No results found. Try ingesting some documents first.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function ResultSection({ title, count, children }: { title: string; count: number; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--accent)' }}>
        {title} ({count})
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {children}
      </div>
    </div>
  );
}

const resultCard: React.CSSProperties = {
  background: 'var(--bg-secondary)',
  border: '1px solid var(--border)',
  borderRadius: '8px',
  padding: '0.75rem 1rem',
};
