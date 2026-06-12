/**
 * App.jsx - Main application with routing and sidebar navigation.
 */
import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import InboxPage from './pages/InboxPage.jsx';
import AnalyticsPage from './pages/AnalyticsPage.jsx';
import ThreadPage from './pages/ThreadPage.jsx';
import AgentPage from './pages/AgentPage.jsx';
import { getDashboardSummary } from './services/api.js';

// Icons as SVG strings
const Icons = {
  inbox: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="nav-icon"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>,
  analytics: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="nav-icon"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>,
  agent: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="nav-icon"><circle cx="12" cy="12" r="10"/><polygon points="10 8 16 12 10 16 10 8"/></svg>,
  shield: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="nav-icon"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>,
};

function Sidebar({ summary }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-text">⚡ SenAI CRM</div>
        <div className="logo-sub">Agentic Intelligence Platform</div>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-section-label">Operations</div>
        <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          {Icons.inbox}
          Inbox
          {summary?.unprocessed > 0 && (
            <span style={{
              marginLeft: 'auto', background: 'var(--gradient-primary)',
              borderRadius: '12px', padding: '2px 8px', fontSize: '10px', fontWeight: '700'
            }}>{summary.unprocessed}</span>
          )}
        </NavLink>
        <NavLink to="/analytics" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          {Icons.analytics}
          Analytics
        </NavLink>

        <div className="nav-section-label">Intelligence</div>
        <NavLink to="/agent" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          {Icons.agent}
          Agent Dry-Run
        </NavLink>
      </nav>
      <div className="sidebar-footer">
        <div className="llm-badge">
          <div className="llm-badge-dot" />
          <span>Groq llama-3.3-70b</span>
        </div>
        {summary && (
          <div style={{ marginTop: 10, fontSize: 11, color: 'var(--color-text-muted)' }}>
            🔴 Legal: {summary.legal_flagged} &nbsp; 🟠 Escalated: {summary.escalated}
          </div>
        )}
      </div>
    </aside>
  );
}

function Header({ title, summary }) {
  return (
    <header className="header">
      <h1 className="header-title">{title}</h1>
      <div className="header-stats">
        {summary?.legal_flagged > 0 && (
          <div className="header-stat">
            <span className="header-stat-label">Legal:</span>
            <span className="header-stat-value danger">{summary.legal_flagged}</span>
          </div>
        )}
        {summary?.escalated > 0 && (
          <div className="header-stat">
            <span className="header-stat-label">Escalated:</span>
            <span className="header-stat-value warning">{summary.escalated}</span>
          </div>
        )}
        <div className="header-stat">
          <span className="header-stat-label">Total:</span>
          <span className="header-stat-value">{summary?.total_emails || 0}</span>
        </div>
      </div>
    </header>
  );
}

function usePageTitle(location) {
  const titles = {
    '/': 'Inbox',
    '/analytics': 'Analytics Dashboard',
    '/agent': 'Agent Dry-Run',
  };
  if (location.pathname.startsWith('/thread/')) return 'Thread Workspace';
  return titles[location.pathname] || 'SenAI CRM';
}

function AppContent() {
  const location = useLocation();
  const [summary, setSummary] = useState(null);
  const title = usePageTitle(location);

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch(() => {});
  }, [location.pathname]);

  return (
    <div className="app-layout">
      <Sidebar summary={summary} />
      <div className="main-content">
        <Header title={title} summary={summary} />
        <div className="page-container animate-in">
          <Routes>
            <Route path="/" element={<InboxPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/thread/:threadId" element={<ThreadPage />} />
            <Route path="/agent" element={<AgentPage />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
