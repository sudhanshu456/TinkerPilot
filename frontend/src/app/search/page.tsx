'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const doSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=10`);
      const data = await res.json();
      setResults(data.results);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const totalResults = results
    ? (results.documents?.length || 0) + (results.tasks?.length || 0) + (results.meetings?.length || 0)
    : 0;

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

          {/* Documents */}
          {results.documents?.length > 0 && (
            <ResultSection title="Documents" count={results.documents.length}>
              {results.documents.map((doc: any, i: number) => (
                <div key={i} style={resultCard}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.3rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--accent)' }}>
                      {doc.filename}{doc.line_start ? `:${doc.line_start}` : ''}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      relevance: {doc.relevance}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {doc.text}
                  </p>
                </div>
              ))}
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
