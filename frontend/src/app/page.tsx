'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';

export default function DashboardPage() {
  const [digest, setDigest] = useState<string>('');
  const [raw, setRaw] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [backendUp, setBackendUp] = useState(false);

  useEffect(() => {
    // Check backend health first
    fetch('/api/health')
      .then((r) => r.json())
      .then(() => {
        setBackendUp(true);
        return fetch('/api/digest');
      })
      .then((r) => r.json())
      .then((data) => {
        setDigest(data.digest);
        setRaw(data.raw);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>Dashboard</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Loading daily digest...</p>
      </div>
    );
  }

  if (!backendUp) {
    return (
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>Dashboard</h1>
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '2rem',
          textAlign: 'center',
        }}>
          <h2 style={{ marginBottom: '1rem' }}>Backend Not Running</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Start the TinkerPilot backend to use the dashboard.
          </p>
          <code style={{
            background: 'var(--bg-tertiary)',
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            display: 'inline-block',
          }}>
            cd backend && python -m cli.main serve
          </code>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>Daily Digest</h1>

      {error && (
        <div style={{
          background: '#1a0a0a',
          border: '1px solid var(--danger)',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1rem',
          color: 'var(--danger)',
        }}>
          {error}
        </div>
      )}

      {digest && (
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
        }}>
          <div className="markdown-content">
            <ReactMarkdown>{digest}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* Quick stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        <StatCard
          title="Pending Tasks"
          value={raw?.tasks?.length ?? 0}
          color="var(--warning)"
        />
        <StatCard
          title="Recent Meetings"
          value={raw?.recent_meetings?.length ?? 0}
          color="var(--accent)"
        />
        <StatCard
          title="Calendar Events"
          value={raw?.calendar?.length ?? 0}
          color="var(--success)"
        />
      </div>
    </div>
  );
}

function StatCard({ title, value, color }: { title: string; value: number; color: string }) {
  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      padding: '1.25rem',
    }}>
      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
        {title}
      </div>
      <div style={{ fontSize: '2rem', fontWeight: 700, color }}>{value}</div>
    </div>
  );
}
