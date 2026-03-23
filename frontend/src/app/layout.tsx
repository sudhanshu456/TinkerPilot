import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';

export const metadata: Metadata = {
  title: 'TinkerPilot',
  description: 'Local AI assistant for developers',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div style={{ display: 'flex', height: '100vh' }}>
          <Sidebar />
          <main style={{ flex: 1, overflow: 'auto', padding: '1.5rem' }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
