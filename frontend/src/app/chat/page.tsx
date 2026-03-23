'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [useRag, setUseRag] = useState(true);
  const [sources, setSources] = useState<any[]>([]);
  const [wsReady, setWsReady] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const streamBuffer = useRef('');

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  // Load history
  useEffect(() => {
    fetch('/api/chat/history?session_id=default')
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setMessages(data.map((m: any) => ({
            role: m.role,
            content: m.content,
            sources: m.sources,
          })));
        }
      })
      .catch(() => {});
  }, []);

  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket('ws://127.0.0.1:8000/ws/chat');

    ws.onopen = () => setWsReady(true);
    ws.onclose = () => {
      setWsReady(false);
      setStreaming(false);
    };
    ws.onerror = () => {
      setWsReady(false);
      setStreaming(false);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case 'token':
          streamBuffer.current += data.content;
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === 'assistant') {
              updated[updated.length - 1] = { ...last, content: streamBuffer.current };
            }
            return updated;
          });
          break;
        case 'sources':
          setSources(data.sources || []);
          break;
        case 'done':
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === 'assistant') {
              updated[updated.length - 1] = { ...last, content: data.full_response, sources };
            }
            return updated;
          });
          setStreaming(false);
          streamBuffer.current = '';
          break;
        case 'error':
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: `Error: ${data.error}` },
          ]);
          setStreaming(false);
          streamBuffer.current = '';
          break;
      }
    };

    wsRef.current = ws;
  }, [sources]);

  const sendMessage = () => {
    if (!input.trim() || streaming) return;

    const userMsg: Message = { role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMsg, { role: 'assistant', content: '' }]);
    setInput('');
    setStreaming(true);
    streamBuffer.current = '';
    setSources([]);

    // Connect WS if needed
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      connectWs();
      // Wait for connection then send
      const interval = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          clearInterval(interval);
          wsRef.current.send(JSON.stringify({
            message: userMsg.content,
            use_rag: useRag,
            session_id: 'default',
          }));
        }
      }, 100);
      setTimeout(() => clearInterval(interval), 5000);
    } else {
      wsRef.current.send(JSON.stringify({
        message: userMsg.content,
        use_rag: useRag,
        session_id: 'default',
      }));
    }
  };

  const clearHistory = () => {
    fetch('/api/chat/history?session_id=default', { method: 'DELETE' })
      .then(() => setMessages([]))
      .catch(() => {});
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 3rem)' }}>
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: '1rem', flexShrink: 0,
      }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Chat</h1>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={useRag}
              onChange={(e) => setUseRag(e.target.checked)}
              style={{ accentColor: 'var(--accent)' }}
            />
            Search docs (RAG)
          </label>
          <button onClick={clearHistory} style={{
            background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
            color: 'var(--text-secondary)', padding: '0.4rem 0.8rem',
            borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem',
          }}>
            Clear
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} style={{
        flex: 1, overflowY: 'auto',
        display: 'flex', flexDirection: 'column', gap: '1rem',
        paddingBottom: '1rem',
      }}>
        {messages.length === 0 && (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            height: '100%', color: 'var(--text-secondary)',
          }}>
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Ask anything about your codebase, docs, or meetings.</p>
              <p style={{ fontSize: '0.85rem' }}>Toggle "Search docs" to use RAG or general knowledge.</p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={{
            display: 'flex',
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
          }}>
            <div style={{
              maxWidth: '80%',
              background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg-secondary)',
              border: msg.role === 'user' ? 'none' : '1px solid var(--border)',
              borderRadius: '12px',
              padding: '0.8rem 1rem',
              color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
            }}>
              {msg.role === 'assistant' ? (
                <div className="markdown-content">
                  <ReactMarkdown>{msg.content || '...'}</ReactMarkdown>
                </div>
              ) : (
                <p>{msg.content}</p>
              )}

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div style={{
                  marginTop: '0.6rem', paddingTop: '0.6rem',
                  borderTop: '1px solid var(--border)', fontSize: '0.8rem',
                }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Sources: </span>
                  {msg.sources.map((s: any, j: number) => (
                    <span key={j} style={{
                      background: 'var(--bg-tertiary)', padding: '0.15rem 0.4rem',
                      borderRadius: '4px', marginRight: '0.3rem', display: 'inline-block',
                      marginBottom: '0.2rem', fontSize: '0.75rem',
                    }}>
                      [{s.index}] {s.filename}{s.line_start ? `:${s.line_start}` : ''}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div style={{
        display: 'flex', gap: '0.5rem', flexShrink: 0,
        background: 'var(--bg-secondary)', border: '1px solid var(--border)',
        borderRadius: '12px', padding: '0.5rem',
      }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          placeholder="Ask a question..."
          disabled={streaming}
          style={{
            flex: 1, background: 'transparent', border: 'none',
            color: 'var(--text-primary)', fontSize: '0.95rem',
            outline: 'none', padding: '0.5rem',
          }}
        />
        <button
          onClick={sendMessage}
          disabled={streaming || !input.trim()}
          style={{
            background: streaming ? 'var(--bg-tertiary)' : 'var(--accent)',
            color: 'white', border: 'none', borderRadius: '8px',
            padding: '0.5rem 1.2rem', cursor: streaming ? 'not-allowed' : 'pointer',
            fontSize: '0.9rem', fontWeight: 600,
          }}
        >
          {streaming ? 'Thinking...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
