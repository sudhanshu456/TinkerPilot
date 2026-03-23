'use client';

import { useEffect, useState } from 'react';

interface Task {
  id: number;
  title: string;
  description: string;
  status: string;
  priority: string;
  due_date: string | null;
  source_type: string | null;
  created_at: string;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filter, setFilter] = useState<string>('');
  const [newTitle, setNewTitle] = useState('');
  const [newPriority, setNewPriority] = useState('medium');
  const [error, setError] = useState('');

  const loadTasks = () => {
    const url = filter ? `/api/tasks?status=${filter}` : '/api/tasks';
    fetch(url)
      .then((r) => r.json())
      .then((data) => setTasks(data.tasks || []))
      .catch((e) => setError(e.message));
  };

  useEffect(() => { loadTasks(); }, [filter]);

  const addTask = async () => {
    if (!newTitle.trim()) return;
    try {
      await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle, priority: newPriority }),
      });
      setNewTitle('');
      loadTasks();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const updateStatus = async (id: number, status: string) => {
    await fetch(`/api/tasks/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    loadTasks();
  };

  const deleteTask = async (id: number) => {
    await fetch(`/api/tasks/${id}`, { method: 'DELETE' });
    loadTasks();
  };

  const statusColors: Record<string, string> = {
    todo: 'var(--text-secondary)',
    in_progress: 'var(--warning)',
    done: 'var(--success)',
  };

  const priorityColors: Record<string, string> = {
    high: 'var(--danger)',
    medium: 'var(--warning)',
    low: 'var(--text-secondary)',
  };

  const grouped = {
    todo: tasks.filter((t) => t.status === 'todo'),
    in_progress: tasks.filter((t) => t.status === 'in_progress'),
    done: tasks.filter((t) => t.status === 'done'),
  };

  return (
    <div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem' }}>Tasks</h1>

      {error && <div style={{ color: 'var(--danger)', marginBottom: '0.5rem', fontSize: '0.85rem' }}>{error}</div>}

      {/* Add task */}
      <div style={{
        display: 'flex', gap: '0.5rem', marginBottom: '1.5rem',
        background: 'var(--bg-secondary)', border: '1px solid var(--border)',
        borderRadius: '8px', padding: '0.5rem',
      }}>
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addTask()}
          placeholder="Add a new task..."
          style={{
            flex: 1, background: 'transparent', border: 'none',
            color: 'var(--text-primary)', outline: 'none', padding: '0.5rem',
            fontSize: '0.9rem',
          }}
        />
        <select
          value={newPriority}
          onChange={(e) => setNewPriority(e.target.value)}
          style={{
            background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
            color: 'var(--text-primary)', borderRadius: '6px', padding: '0.3rem 0.5rem',
            fontSize: '0.8rem',
          }}
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <button onClick={addTask} style={{
          background: 'var(--accent)', color: 'white', border: 'none',
          borderRadius: '6px', padding: '0.5rem 1rem', cursor: 'pointer',
          fontWeight: 600, fontSize: '0.85rem',
        }}>Add</button>
      </div>

      {/* Filter */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {['', 'todo', 'in_progress', 'done'].map((f) => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '0.3rem 0.8rem', borderRadius: '6px', cursor: 'pointer',
            background: filter === f ? 'var(--accent)' : 'var(--bg-tertiary)',
            color: filter === f ? 'white' : 'var(--text-secondary)',
            border: 'none', fontSize: '0.8rem', fontWeight: 500,
          }}>
            {f === '' ? 'All' : f.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Task columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        {(['todo', 'in_progress', 'done'] as const).map((status) => (
          <div key={status}>
            <h3 style={{
              fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.75rem',
              color: statusColors[status], textTransform: 'capitalize',
            }}>
              {status.replace('_', ' ')} ({grouped[status].length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {grouped[status].map((task) => (
                <div key={task.id} style={{
                  background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                  borderRadius: '8px', padding: '0.75rem',
                  borderLeft: `3px solid ${priorityColors[task.priority] || 'var(--border)'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{task.title}</span>
                    <button onClick={() => deleteTask(task.id)} style={{
                      background: 'transparent', border: 'none', color: 'var(--text-secondary)',
                      cursor: 'pointer', fontSize: '0.75rem', padding: '0',
                    }}>x</button>
                  </div>
                  {task.source_type && (
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', display: 'block', marginTop: '0.3rem' }}>
                      from: {task.source_type}
                    </span>
                  )}
                  <div style={{ display: 'flex', gap: '0.3rem', marginTop: '0.5rem' }}>
                    {status !== 'todo' && (
                      <button onClick={() => updateStatus(task.id, 'todo')} style={smallBtn}>Todo</button>
                    )}
                    {status !== 'in_progress' && (
                      <button onClick={() => updateStatus(task.id, 'in_progress')} style={smallBtn}>Start</button>
                    )}
                    {status !== 'done' && (
                      <button onClick={() => updateStatus(task.id, 'done')} style={{...smallBtn, background: 'var(--success)', color: 'white'}}>Done</button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const smallBtn: React.CSSProperties = {
  background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
  color: 'var(--text-secondary)', padding: '0.15rem 0.5rem',
  borderRadius: '4px', cursor: 'pointer', fontSize: '0.7rem',
};
