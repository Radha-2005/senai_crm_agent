/**
 * pages/ThreadPage.jsx - Thread detail workspace with email history and agent output.
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getThread, editDraft, approveDraft } from '../services/api.js';

function DecisionBanner({ decision }) {
  const config = {
    'Legal-Flag': { color: 'alert-danger', emoji: '🚨', msg: 'LEGAL TEAM FLAGGED — Do not reply without Legal approval' },
    'Escalate': { color: 'alert-warning', emoji: '🔺', msg: 'ESCALATED — Assigned to Customer Success Lead' },
    'Auto-Reply': { color: 'alert-success', emoji: '✅', msg: 'AUTO-REPLIED — Draft generated and ready for review' },
    'Human-Review': { color: 'alert-warning', emoji: '👤', msg: 'HUMAN REVIEW REQUIRED — Low confidence classification' },
  };
  const c = config[decision];
  if (!c) return null;
  return (
    <div className={`alert ${c.color}`}>
      {c.emoji} <strong>{c.msg}</strong>
    </div>
  );
}

function AgentSteps({ steps }) {
  if (!steps || steps.length === 0) return null;
  return (
    <div>
      <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        🤖 Agent Reasoning ({steps.length} steps)
      </h3>
      <div className="agent-steps">
        {steps.map((step, i) => (
          <div key={i} className="agent-step">
            <div className="agent-step-num">{step.step ?? i + 1}</div>
            <div style={{ flex: 1 }}>
              {step.tool && (
                <div className="agent-step-tool">→ {step.tool}</div>
              )}
              <div className="agent-step-thought">{step.thought}</div>
              {step.result && step.type === 'final_decision' && (
                <div style={{ marginTop: 6, fontWeight: 600, color: 'var(--color-accent-primary)' }}>
                  Decision: {step.result.decision}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmailCard({ email }) {
  const sentimentColor = {
    critical: 'var(--color-accent-rose)',
    negative: 'var(--color-accent-orange)',
    neutral: 'var(--color-accent-primary)',
    positive: 'var(--color-accent-emerald)',
  };

  return (
    <div style={{
      background: 'rgba(255,255,255,0.03)', border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)', padding: 20, marginBottom: 16,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>{email.subject || '(no subject)'}</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>
            {email.sender_email} · {email.received_at ? new Date(email.received_at).toLocaleString() : 'Unknown date'}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          {email.sentiment && (
            <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 12,
              background: `${sentimentColor[email.sentiment]}20`, color: sentimentColor[email.sentiment],
              border: `1px solid ${sentimentColor[email.sentiment]}40`,
            }}>
              {email.sentiment}
            </span>
          )}
          {email.classification && (
            <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 12,
              background: 'rgba(99,102,241,0.1)', color: '#818cf8',
              border: '1px solid rgba(99,102,241,0.2)',
            }}>
              {email.classification?.replace(/_/g, ' ')}
            </span>
          )}
        </div>
      </div>
      <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
        {email.body || '(empty)'}
      </div>
    </div>
  );
}

function DraftSection({ email, onUpdate }) {
  const [draft, setDraft] = useState(email.draft_reply || '');
  const [saving, setSaving] = useState(false);
  const [approved, setApproved] = useState(email.draft_approved);
  const [msg, setMsg] = useState('');

  const handleSave = async () => {
    setSaving(true);
    try {
      await editDraft(email.id, draft);
      setMsg('✓ Draft saved');
    } catch (e) {
      setMsg('✗ Save failed: ' + e.message);
    } finally {
      setSaving(false);
      setTimeout(() => setMsg(''), 3000);
    }
  };

  const handleApprove = async () => {
    try {
      await approveDraft(email.id);
      setApproved(true);
      setMsg('✓ Draft approved for sending');
      onUpdate?.();
    } catch (e) {
      setMsg('✗ Approval failed: ' + e.message);
    }
  };

  if (!email.draft_reply && !draft) return null;

  return (
    <div className="draft-area">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12, alignItems: 'center' }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          📝 Draft Reply
        </h3>
        {approved && (
          <span style={{ fontSize: 12, color: 'var(--color-accent-emerald)', fontWeight: 600 }}>
            ✅ APPROVED
          </span>
        )}
      </div>
      <textarea
        className="draft-textarea"
        value={draft}
        onChange={e => setDraft(e.target.value)}
        id={`draft-${email.id}`}
        disabled={approved}
        placeholder="Agent draft reply will appear here..."
      />
      {msg && <div style={{ fontSize: 12, color: 'var(--color-accent-emerald)', marginTop: 8 }}>{msg}</div>}
      {!approved && (
        <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
          <button className="btn btn-ghost btn-sm" onClick={handleSave} disabled={saving} id={`save-draft-${email.id}`}>
            {saving ? 'Saving...' : '💾 Save Changes'}
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleApprove} id={`approve-draft-${email.id}`}>
            ✅ Approve & Send
          </button>
        </div>
      )}
    </div>
  );
}

export default function ThreadPage() {
  const { threadId } = useParams();
  const navigate = useNavigate();
  const [thread, setThread] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = () => {
    setLoading(true);
    getThread(threadId)
      .then(setThread)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [threadId]);

  if (loading) return <div className="loading-container"><div className="spinner" /><span>Loading thread...</span></div>;
  if (error) return <div className="alert alert-danger">Error: {error}</div>;
  if (!thread) return <div className="alert alert-warning">Thread not found</div>;

  const lastEmail = thread.emails?.[thread.emails.length - 1];
  const contact = thread.contact;

  return (
    <div>
      <button className="btn btn-ghost btn-sm" onClick={() => navigate('/')} style={{ marginBottom: 20 }} id="back-to-inbox">
        ← Back to Inbox
      </button>

      {/* Thread Header */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>
              {thread.subject || '(no subject)'}
            </h2>
            {contact && (
              <div style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>
                <strong style={{ color: 'var(--color-text-primary)' }}>{contact.name || contact.email}</strong>
                {contact.company && <span> · {contact.company}</span>}
                <span> · {contact.tier} tier</span>
                {contact.ltv > 0 && <span> · LTV: £{contact.ltv.toLocaleString()}</span>}
              </div>
            )}
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 12, padding: '4px 12px', borderRadius: 20,
              background: 'rgba(255,255,255,0.05)', color: 'var(--color-text-secondary)',
              border: '1px solid var(--color-border)',
            }}>
              {thread.emails?.length || 0} email{thread.emails?.length !== 1 ? 's' : ''}
            </span>
            <span style={{ fontSize: 12, padding: '4px 12px', borderRadius: 20,
              background: 'rgba(99,102,241,0.1)', color: '#818cf8',
              border: '1px solid rgba(99,102,241,0.2)',
            }}>
              {thread.status}
            </span>
          </div>
        </div>
      </div>

      {/* Decision Banner */}
      {thread.last_agent_decision && <DecisionBanner decision={thread.last_agent_decision} />}

      <div className="grid-2" style={{ gap: 20 }}>
        {/* Email History */}
        <div>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            📧 Email History
          </h3>
          {thread.emails?.map(email => (
            <EmailCard key={email.id} email={email} />
          ))}
        </div>

        {/* Agent Analysis */}
        <div>
          {lastEmail && (
            <>
              {/* Agent Steps */}
              {lastEmail.agent_steps && <AgentSteps steps={lastEmail.agent_steps} />}
              
              {/* Draft Reply */}
              {lastEmail.draft_reply && (
                <div style={{ marginTop: lastEmail.agent_steps ? 20 : 0 }}>
                  <DraftSection email={lastEmail} onUpdate={load} />
                </div>
              )}

              {/* Classification Details */}
              <div className="card" style={{ marginTop: 20 }}>
                <div className="card-header">
                  <span className="card-title">🔬 Classification</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, fontSize: 13 }}>
                  <div>
                    <div style={{ color: 'var(--color-text-muted)', marginBottom: 4 }}>Type</div>
                    <div style={{ fontWeight: 600 }}>{lastEmail.classification?.replace(/_/g, ' ') || 'pending'}</div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--color-text-muted)', marginBottom: 4 }}>Sentiment</div>
                    <div style={{ fontWeight: 600 }}>{lastEmail.sentiment || 'pending'}</div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--color-text-muted)', marginBottom: 4 }}>Confidence</div>
                    <div style={{ fontWeight: 600 }}>{lastEmail.confidence ? `${(lastEmail.confidence * 100).toFixed(0)}%` : 'N/A'}</div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--color-text-muted)', marginBottom: 4 }}>Decision</div>
                    <div style={{ fontWeight: 600, color: 'var(--color-accent-primary)' }}>{lastEmail.agent_decision || 'pending'}</div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
