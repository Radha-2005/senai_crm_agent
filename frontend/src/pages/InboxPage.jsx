/**
 * pages/InboxPage.jsx - Inbox page showing all email threads.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDashboardInbox } from '../services/api.js';

function getPriorityColor(score) {
  if (score >= 0.9) return 'var(--color-accent-rose)';
  if (score >= 0.7) return 'var(--color-accent-orange)';
  if (score >= 0.4) return 'var(--color-accent-primary)';
  return 'var(--color-text-muted)';
}

function getDecisionBadge(decision) {
  const map = {
    'Legal-Flag': 'badge-legal',
    'Escalate': 'badge-escalated',
    'Auto-Reply': 'badge-auto-reply',
    'Human-Review': 'badge-human-review',
    'Ignore': 'badge-closed',
  };
  return map[decision] || 'badge-open';
}

function getSentimentBadge(sentiment) {
  const map = {
    critical: 'badge-critical',
    negative: 'badge-negative',
    neutral: 'badge-neutral',
    positive: 'badge-positive',
  };
  return map[sentiment] || 'badge-neutral';
}

function StatusFilter({ current, onChange }) {
  const filters = [
    { value: '', label: 'All' },
    { value: 'open', label: '🔵 Open' },
    { value: 'escalated', label: '🟠 Escalated' },
    { value: 'legal_flagged', label: '🔴 Legal' },
    { value: 'auto_replied', label: '🟢 Auto-Replied' },
    { value: 'human_review', label: '🟡 Human Review' },
  ];

  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
      {filters.map(f => (
        <button
          key={f.value}
          onClick={() => onChange(f.value)}
          className={`btn btn-sm ${current === f.value ? 'btn-primary' : 'btn-ghost'}`}
          id={`filter-${f.value || 'all'}`}
        >
          {f.label}
        </button>
      ))}
    </div>
  );
}

export default function InboxPage() {
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    getDashboardInbox(100)
      .then(data => setThreads(data.threads || []))
      .catch(() => setThreads([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = threads.filter(t => {
    if (filter && t.status !== filter) return false;
    if (search) {
      const q = search.toLowerCase();
      return (
        t.subject?.toLowerCase().includes(q) ||
        t.contact_name?.toLowerCase().includes(q) ||
        t.contact_email?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <span>Loading inbox...</span>
      </div>
    );
  }

  return (
    <div>
      {/* Toolbar */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
        <input
          type="search"
          placeholder="Search threads, contacts..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          id="inbox-search"
          style={{
            flex: 1, padding: '10px 16px', background: 'var(--color-bg-card)',
            border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)',
            color: 'var(--color-text-primary)', fontSize: 13, outline: 'none',
            fontFamily: 'Inter, sans-serif',
          }}
        />
        <div style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>
          {filtered.length} threads
        </div>
      </div>

      <StatusFilter current={filter} onChange={setFilter} />

      {/* Thread list */}
      <div className="card" style={{ padding: 0 }}>
        {filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <div className="empty-state-text">
              {search || filter ? 'No threads match your filter' : 'No threads yet. Ingest emails to get started.'}
            </div>
          </div>
        ) : (
          filtered.map(thread => (
            <div
              key={thread.thread_id}
              className="inbox-row"
              id={`thread-${thread.thread_id}`}
              onClick={() => navigate(`/thread/${thread.thread_id}`)}
            >
              <div
                className="inbox-priority"
                style={{ background: getPriorityColor(thread.priority_score) }}
              />
              <div className="inbox-content">
                <div className="inbox-subject">{thread.subject || '(no subject)'}</div>
                <div className="inbox-meta">
                  <span style={{ color: 'var(--color-text-primary)', fontWeight: 500 }}>
                    {thread.contact_name || 'Unknown'}
                  </span>
                  <span>·</span>
                  <span>{thread.contact_email}</span>
                  <span>·</span>
                  <span>{thread.email_count} email{thread.email_count !== 1 ? 's' : ''}</span>
                  <span>·</span>
                  <span>{new Date(thread.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
              <div className="inbox-actions">
                {thread.latest_sentiment && (
                  <span className={`badge ${getSentimentBadge(thread.latest_sentiment)}`}>
                    {thread.latest_sentiment}
                  </span>
                )}
                {thread.last_decision ? (
                  <span className={`badge ${getDecisionBadge(thread.last_decision)}`}>
                    {thread.last_decision}
                  </span>
                ) : (
                  <span className="badge badge-open">pending</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
