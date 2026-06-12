/**
 * pages/AnalyticsPage.jsx - Analytics dashboard with charts and metrics.
 */
import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { getDashboardStats } from '../services/api.js';

const COLORS = ['#6366f1', '#f43f5e', '#10b981', '#f59e0b', '#06b6d4', '#8b5cf6', '#f97316'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'rgba(13,18,38,0.95)', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ color: 'rgba(255,255,255,0.6)', marginBottom: 4 }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.fill || p.color || '#fff', fontWeight: 600 }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
};

export default function AnalyticsPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDashboardStats()
      .then(setStats)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-container"><div className="spinner" /><span>Loading analytics...</span></div>;
  if (error) return <div className="alert alert-danger">Error loading analytics: {error}</div>;
  if (!stats) return null;

  const sentimentData = stats.sentiment_breakdown?.map(s => ({
    name: s.label, value: s.count,
  })) || [];

  const classificationData = stats.classification_breakdown?.slice(0, 7).map(c => ({
    name: c.label.replace(/_/g, ' '), count: c.count, pct: c.percentage,
  })) || [];

  const decisionData = Object.entries(stats.decision_breakdown || {}).map(([k, v]) => ({
    name: k, count: v,
  }));

  return (
    <div>
      {/* KPI Stats */}
      <div className="stats-grid">
        <div className="stat-card" style={{ '--stat-accent': 'var(--gradient-primary)' }}>
          <div className="stat-card-icon">📧</div>
          <div className="stat-card-value">{stats.total_emails?.toLocaleString() || 0}</div>
          <div className="stat-card-label">Total Emails</div>
        </div>
        <div className="stat-card" style={{ '--stat-accent': 'var(--gradient-info)' }}>
          <div className="stat-card-icon">☀️</div>
          <div className="stat-card-value">{stats.processed_today || 0}</div>
          <div className="stat-card-label">Processed Today</div>
        </div>
        <div className="stat-card" style={{ '--stat-accent': 'var(--gradient-warning)' }}>
          <div className="stat-card-icon">⏳</div>
          <div className="stat-card-value">{stats.pending || 0}</div>
          <div className="stat-card-label">Pending</div>
        </div>
        <div className="stat-card" style={{ '--stat-accent': 'var(--gradient-danger)' }}>
          <div className="stat-card-icon">🚨</div>
          <div className="stat-card-value">{stats.legal_flagged || 0}</div>
          <div className="stat-card-label">Legal Flagged</div>
        </div>
        <div className="stat-card" style={{ '--stat-accent': 'linear-gradient(135deg, #f97316, #ea580c)' }}>
          <div className="stat-card-icon">🔺</div>
          <div className="stat-card-value">{stats.escalated || 0}</div>
          <div className="stat-card-label">Escalated</div>
        </div>
        <div className="stat-card" style={{ '--stat-accent': 'var(--gradient-success)' }}>
          <div className="stat-card-icon">✅</div>
          <div className="stat-card-value">{stats.auto_replied || 0}</div>
          <div className="stat-card-label">Auto-Replied</div>
        </div>
      </div>

      {/* Charts row */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Classification breakdown */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Email Classification Breakdown</span>
          </div>
          {classificationData.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">📊</div><div>No data yet</div></div>
          ) : (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={classificationData} layout="vertical" margin={{ left: 10, right: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis type="number" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} width={110} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]}>
                    {classificationData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Sentiment breakdown */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Sentiment Distribution</span>
          </div>
          {sentimentData.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">😐</div><div>No data yet</div></div>
          ) : (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sentimentData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {sentimentData.map((entry, i) => {
                      const colors = { critical: '#f43f5e', negative: '#f97316', neutral: '#6366f1', positive: '#10b981' };
                      return <Cell key={i} fill={colors[entry.name] || COLORS[i]} />;
                    })}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    formatter={(value) => <span style={{ color: '#94a3b8', fontSize: 12 }}>{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Agent Decision Breakdown */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Agent Decision Breakdown</span>
        </div>
        {decisionData.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">🤖</div><div>No decisions yet</div></div>
        ) : (
          <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            {decisionData.map((d, i) => {
              const decisionColors = {
                'Legal-Flag': '#f43f5e',
                'Escalate': '#f97316',
                'Auto-Reply': '#10b981',
                'Human-Review': '#f59e0b',
                'Ignore': '#475569',
              };
              const color = decisionColors[d.name] || '#6366f1';
              const total = decisionData.reduce((s, x) => s + x.count, 0);
              const pct = total > 0 ? ((d.count / total) * 100).toFixed(1) : 0;
              return (
                <div key={d.name} style={{
                  flex: '1 1 160px', padding: '20px', background: `${color}15`,
                  border: `1px solid ${color}30`, borderRadius: 12, textAlign: 'center',
                }}>
                  <div style={{ fontSize: 28, fontWeight: 700, color, fontFamily: 'Space Grotesk' }}>{d.count}</div>
                  <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>{d.name}</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color, marginTop: 4 }}>{pct}%</div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
