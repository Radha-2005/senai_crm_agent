# API Documentation — SenAI Platform

## API Overview
SenAI exposes a RESTful API for integrations. All requests must use HTTPS and authenticate via API key.

---

## Authentication
All API requests must include the API key in the header:
```
Authorization: Bearer YOUR_API_KEY
X-Workspace-ID: your-workspace-id
```

**Important:** v2 API requires BOTH `Authorization` AND `X-Workspace-ID` headers. v1 only required `Authorization`.

---

## API Rate Limits by Tier

| Tier       | Rate Limit         | Burst Limit | Daily Cap    |
|------------|--------------------|-------------|--------------|
| Free       | 100 req/min        | 200 req/min | 10,000/day   |
| Standard   | 1,000 req/min      | 2,000 req/min | 500,000/day |
| Pro        | 5,000 req/min      | 10,000 req/min | 2,000,000/day |
| Enterprise | Custom (default 10,000 req/min) | Negotiable | Unlimited |

Rate limit headers returned on every response:
- `X-RateLimit-Limit`: Your tier limit
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

**429 Too Many Requests** is returned when rate limit is exceeded. Implement exponential backoff.

---

## API v1 Deprecation

**⚠️ API v1 will be sunset on December 31, 2023.**

All integrations must migrate to API v2 before this date.

### v2 Breaking Changes from v1:
1. **New Auth Header**: `X-Workspace-ID` is now required (not just `Authorization`)
2. **Paginated Responses**: All list endpoints now return paginated format:
   ```json
   { "data": [...], "pagination": { "page": 1, "per_page": 50, "total": 243, "next_cursor": "abc123" } }
   ```
3. **Webhook Signature Validation**: Webhooks now require HMAC-SHA256 signature in `X-SenAI-Signature` header
4. **Endpoint Changes**:
   - `/v1/events` → `/v2/events` (POST body schema changed)
   - `/v1/users` → `/v2/contacts` (renamed)
   - `/v1/tickets` → `/v2/threads` (restructured)

### Migration Guide:
1. Obtain `X-Workspace-ID` from your account settings
2. Update all endpoint paths from `/v1/` to `/v2/`
3. Update response parsing for paginated format
4. Implement webhook signature validation
5. Test in sandbox before production cutover

---

## Key Endpoints

### POST /v2/events
Submit events to the platform.
- Requires: `Authorization`, `X-Workspace-ID`
- Returns: `{ "event_id": "...", "status": "queued" }`

### GET /v2/contacts
List contacts with pagination.
- Params: `page`, `per_page`, `filter[status]`

### POST /v2/threads/{id}/reply
Send a reply to a thread.
- Body: `{ "content": "...", "type": "email|note" }`

### GET /v2/analytics/sentiment
Time-series sentiment data.
- Params: `sender`, `days`, `granularity`

---

## Webhook Events
SenAI sends webhook events for:
- `email.received` — New email ingested
- `email.classified` — Classification complete
- `email.escalated` — Email escalated to human
- `thread.resolved` — Thread marked resolved
- `contact.churn_risk` — Churn risk score changed

All webhooks include `X-SenAI-Signature` for validation.

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_MISSING` | 401 | No API key provided |
| `AUTH_INVALID` | 401 | Invalid or expired API key |
| `WORKSPACE_MISSING` | 400 | X-Workspace-ID header missing (v2 only) |
| `RATE_LIMITED` | 429 | Rate limit exceeded |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request body validation failed |
| `DUPLICATE_ID` | 409 | message_id already exists (idempotent) |
