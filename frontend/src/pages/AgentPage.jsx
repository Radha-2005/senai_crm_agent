/**
 * pages/AgentPage.jsx - Agent dry-run evaluation page.
 * Allows running the 6 evaluation scenarios and manual triage.
 */
import React, { useState } from 'react';
import { runDryRun, manualTriage } from '../services/api.js';

const SCENARIOS = [
  { id: 'gdpr', name: 'GDPR Data Request', expected: 'Legal-Flag', icon: '🔏',
    subject: 'GDPR Right to Data Portability Request',
    body: 'I am formally requesting data portability under GDPR Article 20.' },
  { id: 'ransom', name: 'Ransomware Threat', expected: 'Legal-Flag', icon: '💀',
    subject: 'Pay Ransom or Data Gets Published',
    body: 'We have compromised your systems. Pay 5 BTC ransomware demand.' },
  { id: 'refund', name: 'Karen Refund Risk', expected: 'Escalate', icon: '😤',
    subject: 'Final Warning - Full Refund NOW',
    body: 'This is my final warning. I am furious. Give me a refund or I sue.' },
  { id: 'chatbot', name: 'Chatbot Misinformation', expected: 'Escalate', icon: '🤖',
    subject: 'Your Chatbot Gave Wrong Refund Info',
    body: 'Your chatbot told me I could get a 60-day refund. Now you say 14 days. Your AI misinformed me.' },
  { id: 'sla', name: 'Bob SLA Legal', expected: 'Legal-Flag', icon: '⚖️',
    subject: 'SLA Breach - Legal Action Pending',
    body: 'You breached our SLA. My attorney has been notified. Pursuing legal action for SLA breach.' },
  { id: 'pricing', name: 'Alice Pricing Upgrade', expected: 'Auto-Reply', icon: '💡',
    subject: 'Enterprise Upgrade - 10 Seats Pro-rata',
    body: 'I would like to upgrade to Enterprise and add 10 seats mid-cycle. What is the pricing?' },
];

function ScenarioCard({ scenario, result, running, onRun }) {
  const passed = result?.actual_decision === scenario.expected;
  return (
    <div style={{
      background: 'var(--color-bg-card)', border: `1px solid ${
        result ? (passed ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.3)') : 'var(--color-border)'
      }`, borderRadius: 'var(--radius-md)', padding: 20, transition: 'all 0.2s',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 20, marginBottom: 6 }}>{scenario.icon}</div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>{scenario.name}</div>
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>
            Expected: <strong style={{ color: 'var(--color-accent-primary)' }}>{scenario.expected}</strong>
          </div>
        </div>
        {result && (
          <div style={{ fontSize: 22 }}>{passed ? '✅' : '❌'}</div>
        )}
      </div>

      {result && (
        <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
          <div>Got: <strong style={{ color: passed ? 'var(--color-accent-emerald)' : 'var(--color-accent-rose)' }}>
            {result.actual_decision}
          </strong></div>
          <div>Class: {result.classification} · Sentiment: {result.sentiment}</div>
          <div>Confidence: {result.confidence ? `${(result.confidence * 100).toFixed(0)}%` : 'N/A'}</div>
        </div>
      )}

      <button
        className="btn btn-ghost btn-sm"
        onClick={() => onRun(scenario)}
        disabled={running}
        id={`run-scenario-${scenario.id}`}
        style={{ width: '100%', justifyContent: 'center' }}
      >
        {running ? '⏳ Running...' : '▶ Run Scenario'}
      </button>
    </div>
  );
}

export default function AgentPage() {
  const [results, setResults] = useState({});
  const [running, setRunning] = useState(null);
  const [allRunning, setAllRunning] = useState(false);
  const [customSubject, setCustomSubject] = useState('');
  const [customBody, setCustomBody] = useState('');
  const [customEmail, setCustomEmail] = useState('test@example.com');
  const [customResult, setCustomResult] = useState(null);
  const [customRunning, setCustomRunning] = useState(false);

  const handleRunAll = async () => {
    setAllRunning(true);
    setResults({});
    try {
      const data = await runDryRun();
      const mapped = {};
      (data.results || []).forEach(r => {
        const sc = SCENARIOS.find(s => r.scenario_id.includes(s.id));
        if (sc) mapped[sc.id] = r;
      });
      // Map by scenario_id
      (data.results || []).forEach(r => {
        const sc = SCENARIOS.find(s => r.scenario_id === `test_${s.id}_01`);
        if (sc) mapped[sc.id] = r;
      });
      setResults(mapped);
    } catch (e) {
      alert('Failed to run dry-run: ' + e.message);
    } finally {
      setAllRunning(false);
    }
  };

  const handleRunOne = async (scenario) => {
    setRunning(scenario.id);
    try {
      const result = await manualTriage({
        subject: scenario.subject,
        body: scenario.body,
        sender_email: `test-${scenario.id}@example.com`,
        dry_run: true,
      });
      setResults(prev => ({
        ...prev,
        [scenario.id]: {
          actual_decision: result.decision,
          expected_decision: scenario.expected,
          classification: result.classification,
          sentiment: result.sentiment,
          confidence: result.confidence,
          passed: result.decision === scenario.expected,
        },
      }));
    } catch (e) {
      alert('Triage failed: ' + e.message);
    } finally {
      setRunning(null);
    }
  };

  const handleCustomTriage = async () => {
    if (!customSubject || !customBody) return;
    setCustomRunning(true);
    setCustomResult(null);
    try {
      const result = await manualTriage({
        subject: customSubject,
        body: customBody,
        sender_email: customEmail,
        dry_run: true,
      });
      setCustomResult(result);
    } catch (e) {
      alert('Triage failed: ' + e.message);
    } finally {
      setCustomRunning(false);
    }
  };

  const passedCount = Object.values(results).filter(r => r.passed).length;
  const totalRan = Object.keys(results).length;

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 24 }}>
        <button
          className="btn btn-primary"
          onClick={handleRunAll}
          disabled={allRunning}
          id="run-all-scenarios"
        >
          {allRunning ? '⏳ Running All...' : '▶▶ Run All 6 Scenarios'}
        </button>
        {totalRan > 0 && (
          <div style={{ fontSize: 14, fontWeight: 600 }}>
            <span style={{ color: passedCount === totalRan ? 'var(--color-accent-emerald)' : 'var(--color-accent-rose)' }}>
              {passedCount}/{totalRan} passed
            </span>
          </div>
        )}
      </div>

      {/* Scenario Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginBottom: 32 }}>
        {SCENARIOS.map(sc => (
          <ScenarioCard
            key={sc.id}
            scenario={sc}
            result={results[sc.id]}
            running={running === sc.id || allRunning}
            onRun={handleRunOne}
          />
        ))}
      </div>

      {/* Custom Triage */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">🧪 Custom Email Triage</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input
            type="email"
            placeholder="Sender email"
            value={customEmail}
            onChange={e => setCustomEmail(e.target.value)}
            id="custom-sender"
            style={{
              padding: '10px 14px', background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--color-border)', borderRadius: 8,
              color: 'var(--color-text-primary)', fontSize: 13, outline: 'none',
              fontFamily: 'Inter, sans-serif',
            }}
          />
          <input
            type="text"
            placeholder="Email subject"
            value={customSubject}
            onChange={e => setCustomSubject(e.target.value)}
            id="custom-subject"
            style={{
              padding: '10px 14px', background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--color-border)', borderRadius: 8,
              color: 'var(--color-text-primary)', fontSize: 13, outline: 'none',
              fontFamily: 'Inter, sans-serif',
            }}
          />
          <textarea
            placeholder="Email body..."
            value={customBody}
            onChange={e => setCustomBody(e.target.value)}
            id="custom-body"
            rows={5}
            style={{
              padding: '10px 14px', background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--color-border)', borderRadius: 8,
              color: 'var(--color-text-primary)', fontSize: 13, outline: 'none',
              resize: 'vertical', fontFamily: 'Inter, sans-serif',
            }}
          />
          <button
            className="btn btn-primary"
            onClick={handleCustomTriage}
            disabled={customRunning || !customSubject || !customBody}
            id="run-custom-triage"
          >
            {customRunning ? '⏳ Analyzing...' : '🔍 Run Triage'}
          </button>
        </div>

        {customResult && (
          <div style={{ marginTop: 20, padding: 16, background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid var(--color-border)' }}>
            <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 12 }}>
              Decision:{' '}
              <span style={{
                color: {
                  'Legal-Flag': 'var(--color-accent-rose)',
                  'Escalate': 'var(--color-accent-orange)',
                  'Auto-Reply': 'var(--color-accent-emerald)',
                  'Human-Review': 'var(--color-accent-amber)',
                }[customResult.decision] || 'var(--color-accent-primary)',
              }}>
                {customResult.decision}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, fontSize: 13 }}>
              <div>
                <div style={{ color: 'var(--color-text-muted)', marginBottom: 4 }}>Classification</div>
                <strong>{customResult.classification?.replace(/_/g, ' ')}</strong>
              </div>
              <div>
                <div style={{ color: 'var(--color-text-muted)', marginBottom: 4 }}>Sentiment</div>
                <strong>{customResult.sentiment}</strong>
              </div>
              <div>
                <div style={{ color: 'var(--color-text-muted)', marginBottom: 4 }}>Confidence</div>
                <strong>{customResult.confidence ? `${(customResult.confidence * 100).toFixed(0)}%` : 'N/A'}</strong>
              </div>
            </div>

            {customResult.steps?.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Agent Steps ({customResult.steps.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {customResult.steps.slice(0, 5).map((step, i) => (
                    <div key={i} style={{ fontSize: 12, color: 'var(--color-text-secondary)', padding: '6px 10px', background: 'rgba(255,255,255,0.03)', borderRadius: 6 }}>
                      <span style={{ color: 'var(--color-accent-cyan)', fontWeight: 600 }}>
                        {step.tool ? `[${step.tool}]` : `[${step.type}]`}
                      </span>{' '}
                      {step.thought?.slice(0, 100)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
