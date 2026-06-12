/**
 * services/api.js - API client for the SenAI CRM backend.
 * All backend calls go through this module.
 */

const BASE_URL = '/api/v1';

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// --- Health ---
export const getHealth = () => request('/health');
export const getStatus = () => request('/status');

// --- Dashboard ---
export const getDashboardSummary = () => request('/dashboard/summary');
export const getDashboardInbox = (limit = 50) => request(`/dashboard/inbox?limit=${limit}`);

// --- Analytics ---
export const getDashboardStats = () => request('/analytics/dashboard');

// --- Threads ---
export const listThreads = (status, page = 1, perPage = 20) => {
  const params = new URLSearchParams({ page, per_page: perPage });
  if (status) params.append('status', status);
  return request(`/threads?${params}`);
};
export const getThread = (id) => request(`/threads/${id}`);

// --- Emails ---
export const getEmail = (id) => request(`/emails/${id}`);
export const editDraft = (id, draftReply) =>
  request(`/emails/${id}/draft`, {
    method: 'PATCH',
    body: JSON.stringify({ draft_reply: draftReply }),
  });
export const approveDraft = (id) =>
  request(`/emails/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ approved: true }),
  });

// --- Contacts ---
export const listContacts = (page = 1) => request(`/contacts?page=${page}`);
export const getContact = (id) => request(`/contacts/${id}`);

// --- Agent ---
export const runDryRun = () => request('/agent/dry-run');
export const manualTriage = (payload) =>
  request('/agent/triage/manual', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// --- RAG ---
export const searchKB = (query, n = 3) =>
  request('/rag/search', {
    method: 'POST',
    body: JSON.stringify({ query, n_results: n }),
  });
export const getKBStats = () => request('/rag/stats');
export const reseedKB = () =>
  request('/rag/seed', { method: 'POST' });

// --- Ingest ---
export const ingestEmail = (payload) =>
  request('/ingest', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
