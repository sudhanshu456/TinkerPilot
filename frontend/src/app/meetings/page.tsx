'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface Meeting {
  id: number;
  title: string;
  date: string;
  duration_seconds: number;
  language: string;
  has_summary: boolean;
  created_at: string;
}

interface MeetingDetail {
  id: number;
  title: string;
  date: string;
  transcript: string;
  summary: any;
  duration_seconds: number;
}

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [selected, setSelected] = useState<MeetingDetail | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'summary' | 'transcript'>('summary');

  const loadMeetings = () => {
    fetch('/api/meetings')
      .then((r) => r.json())
      .then((data) => setMeetings(data.meetings || []))
      .catch((e) => setError(e.message));
  };

  useEffect(() => { loadMeetings(); }, []);

  const loadMeeting = (id: number) => {
    fetch(`/api/meetings/${id}`)
      .then((r) => r.json())
      .then((data) => { setSelected(data); setTab('summary'); })
      .catch((e) => setError(e.message));
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError('');
    const form = new FormData();
    form.append('file', file);
    form.append('title', file.name);

    try {
      const res = await fetch('/api/meetings/transcribe', { method: 'POST', body: form });
      if (!res.ok) throw new Error('Transcription failed');
      const data = await res.json();
      loadMeetings();
      setSelected({
        id: data.meeting_id,
        title: file.name,
        date: new Date().toISOString(),
        transcript: data.transcript,
        summary: data.summary,
        duration_seconds: data.duration_seconds,
      });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const deleteMeeting = async (id: number) => {
    await fetch(`/api/meetings/${id}`, { method: 'DELETE' });
    if (selected?.id === id) setSelected(null);
    loadMeetings();
  };

  const formatDuration = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
  };

  return (
    <div style={{ display: 'flex', gap: '1.5rem', height: 'calc(100vh - 3rem)' }}>
      {/* Sidebar list */}
      <div style={{ width: '280px', flexShrink: 0, display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Meetings</h1>
        </div>

        {/* Upload */}
        <label style={{
          display: 'block', textAlign: 'center', padding: '0.8rem',
          background: 'var(--accent)', borderRadius: '8px',
          cursor: uploading ? 'not-allowed' : 'pointer', marginBottom: '1rem',
          color: 'white', fontWeight: 600, fontSize: '0.9rem',
          opacity: uploading ? 0.6 : 1,
        }}>
          {uploading ? 'Transcribing...' : 'Upload Audio'}
          <input type="file" accept="audio/*" onChange={handleUpload} hidden disabled={uploading} />
        </label>

        {error && (
          <div style={{ color: 'var(--danger)', fontSize: '0.8rem', marginBottom: '0.5rem' }}>{error}</div>
        )}

        {/* Meeting list */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {meetings.length === 0 && (
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', textAlign: 'center', padding: '2rem 0' }}>
              No meetings yet. Upload an audio file.
            </p>
          )}
          {meetings.map((m) => (
            <div
              key={m.id}
              onClick={() => loadMeeting(m.id)}
              style={{
                padding: '0.75rem', borderRadius: '8px', cursor: 'pointer',
                marginBottom: '0.5rem',
                background: selected?.id === m.id ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
                border: selected?.id === m.id ? '1px solid var(--accent)' : '1px solid var(--border)',
              }}
            >
              <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.2rem' }}>{m.title}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                {m.date?.slice(0, 10)} {m.duration_seconds > 0 && `- ${formatDuration(m.duration_seconds)}`}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detail panel */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {!selected ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-secondary)' }}>
            Select a meeting or upload audio to get started.
          </div>
        ) : (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700 }}>{selected.title}</h2>
              <button onClick={() => deleteMeeting(selected.id)} style={{
                background: 'transparent', border: '1px solid var(--danger)', color: 'var(--danger)',
                padding: '0.3rem 0.8rem', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem',
              }}>Delete</button>
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
              {(['summary', 'transcript'] as const).map((t) => (
                <button key={t} onClick={() => setTab(t)} style={{
                  padding: '0.4rem 1rem', borderRadius: '6px', cursor: 'pointer',
                  background: tab === t ? 'var(--accent)' : 'var(--bg-tertiary)',
                  color: tab === t ? 'white' : 'var(--text-secondary)',
                  border: 'none', fontWeight: 600, fontSize: '0.85rem',
                  textTransform: 'capitalize',
                }}>{t}</button>
              ))}
            </div>

            {/* Content */}
            <div style={{
              background: 'var(--bg-secondary)', border: '1px solid var(--border)',
              borderRadius: '8px', padding: '1.5rem',
            }}>
              {tab === 'summary' && selected.summary ? (
                <div>
                  {typeof selected.summary === 'string' ? (
                    <div className="markdown-content"><ReactMarkdown>{selected.summary}</ReactMarkdown></div>
                  ) : (
                    <div>
                      {selected.summary.summary && (
                        <div style={{ marginBottom: '1rem' }}>
                          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--accent)' }}>Summary</h3>
                          <p>{selected.summary.summary}</p>
                        </div>
                      )}
                      {selected.summary.key_topics?.length > 0 && (
                        <div style={{ marginBottom: '1rem' }}>
                          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--accent)' }}>Key Topics</h3>
                          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                            {selected.summary.key_topics.map((t: string, i: number) => (
                              <span key={i} style={{ background: 'var(--bg-tertiary)', padding: '0.2rem 0.6rem', borderRadius: '12px', fontSize: '0.8rem' }}>{t}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      {selected.summary.decisions?.length > 0 && (
                        <div style={{ marginBottom: '1rem' }}>
                          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--accent)' }}>Decisions</h3>
                          <ul style={{ paddingLeft: '1.2rem' }}>
                            {selected.summary.decisions.map((d: string, i: number) => <li key={i} style={{ marginBottom: '0.3rem' }}>{d}</li>)}
                          </ul>
                        </div>
                      )}
                      {selected.summary.action_items?.length > 0 && (
                        <div style={{ marginBottom: '1rem' }}>
                          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--warning)' }}>Action Items</h3>
                          <ul style={{ paddingLeft: '1.2rem' }}>
                            {selected.summary.action_items.map((a: any, i: number) => (
                              <li key={i} style={{ marginBottom: '0.3rem' }}>
                                {typeof a === 'string' ? a : `${a.task} ${a.assignee ? `(${a.assignee})` : ''} [${a.priority || 'medium'}]`}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {selected.summary.follow_ups?.length > 0 && (
                        <div>
                          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--accent)' }}>Follow-ups</h3>
                          <ul style={{ paddingLeft: '1.2rem' }}>
                            {selected.summary.follow_ups.map((f: string, i: number) => <li key={i} style={{ marginBottom: '0.3rem' }}>{f}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : tab === 'transcript' ? (
                <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', lineHeight: 1.6, fontSize: '0.9rem' }}>
                  {selected.transcript || 'No transcript available.'}
                </pre>
              ) : (
                <p style={{ color: 'var(--text-secondary)' }}>No summary available.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
