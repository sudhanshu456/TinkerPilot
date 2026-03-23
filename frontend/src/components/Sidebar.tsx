'use client';

const links = [
  { href: '/', label: 'Dashboard', icon: '~' },
  { href: '/chat', label: 'Chat', icon: '>' },
  { href: '/meetings', label: 'Meetings', icon: '#' },
  { href: '/tasks', label: 'Tasks', icon: '+' },
  { href: '/search', label: 'Search', icon: '?' },
  { href: '/settings', label: 'Settings', icon: '*' },
];

export default function Sidebar() {
  return (
    <nav style={{
      width: '200px',
      background: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border)',
      padding: '1rem 0',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
    }}>
      <div style={{
        padding: '0 1rem 1rem',
        borderBottom: '1px solid var(--border)',
        marginBottom: '0.5rem',
      }}>
        <h1 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent)' }}>
          TinkerPilot
        </h1>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Local AI Assistant</span>
      </div>
      {links.map((link) => (
        <a
          key={link.href}
          href={link.href}
          className="sidebar-link"
          style={{
            display: 'block',
            padding: '0.6rem 1rem',
            color: 'var(--text-secondary)',
            textDecoration: 'none',
            fontSize: '0.9rem',
            transition: 'all 0.15s',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.background = 'var(--bg-tertiary)';
            e.currentTarget.style.color = 'var(--text-primary)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'var(--text-secondary)';
          }}
        >
          <span style={{ marginRight: '0.5rem', fontFamily: 'monospace' }}>{link.icon}</span>
          {link.label}
        </a>
      ))}
    </nav>
  );
}
