# Compliance FAQ — SenAI Platform

## HIPAA Compliance

### Do you offer HIPAA Business Associate Agreements (BAAs)?
**Yes.** SenAI offers HIPAA BAAs to customers on the Enterprise plan who process Protected Health Information (PHI). BAAs are available upon request and must be signed before using SenAI in a clinical or healthcare setting.

### Is data encrypted at rest and in transit?
- **In Transit:** All data is encrypted using TLS 1.3. We do not support TLS 1.0 or 1.1.
- **At Rest:** All data is encrypted using AES-256. Database volumes and backups are encrypted.

### Where are your servers hosted?
SenAI is hosted on AWS in US-East-1 (primary) and EU-West-1 (EU data residency option). Customers on Enterprise plans can request dedicated EU data residency. Healthcare customers can request US-only data residency.

### What HIPAA controls do you have in place?
- Access controls with role-based permissions and MFA
- Audit logging for all data access events
- Automatic session timeout after 15 minutes of inactivity
- Data minimization: only process data required for the service
- Employee HIPAA training and background checks
- Incident response plan with <1 hour notification SLA for PHI breaches

### HIPAA BAA Process:
1. Customer requests BAA via enterprise@senai.io
2. Legal review (typically 2-3 business days)
3. BAA executed and stored
4. HIPAA-compliant features enabled on account

---

## GDPR Compliance

### Are you GDPR compliant?
**Yes.** SenAI acts as a Data Processor under GDPR when processing your customers' data. You (the customer) are the Data Controller.

### Do you offer a Data Processing Agreement (DPA)?
**Yes.** A DPA is available for all customers. Enterprise customers get a customized DPA. Email dpo@senai.io to request.

### Data Subject Requests (DSRs)
SenAI supports all GDPR rights:
- **Article 15 (Access):** Export available within 30 days
- **Article 17 (Erasure / Right to Be Forgotten):** Data deletion within 30 days
- **Article 20 (Data Portability):** Machine-readable export (JSON/CSV) within 30 days
- **Article 21 (Objection):** Contact dpo@senai.io

**Statutory Deadline:** All GDPR data subject requests must be fulfilled within **30 calendar days** of receipt.

### Data Residency
- Default: US-East-1 (AWS)
- EU Option: EU-West-1 (Ireland) — available on Enterprise plan
- Data never transferred outside contracted region without explicit consent

### Third-Party Sub-processors
SenAI uses these sub-processors (full list at senai.io/sub-processors):
- AWS (infrastructure)
- Groq/OpenAI (LLM processing — data not used for training)
- Stripe (billing)

---

## SOC 2 Type II

### Are you SOC 2 Type II certified?
**Yes.** SenAI maintains a SOC 2 Type II report covering Trust Service Criteria: Security, Availability, and Confidentiality. The audit period covers the last 12 months.

### Can I request the SOC 2 report?
Yes. Enterprise customers can request a copy of our SOC 2 Type II report under NDA. Contact security@senai.io.

### What controls are covered?
- CC1-CC9: Common Criteria (Security)
- A1: Availability (99.9% uptime SLA)
- C1-C2: Confidentiality controls

---

## ISO 27001

SenAI is currently ISO 27001 certified. Certificate available upon request for Enterprise customers.

---

## Penetration Testing

SenAI conducts annual third-party penetration tests. Executive summary of the most recent pentest is available to Enterprise customers under NDA. Contact security@senai.io.

---

## Data Retention

| Data Type | Retention Period |
|-----------|-----------------|
| Email content | 2 years (configurable) |
| Audit logs | 7 years |
| Analytics data | 3 years |
| Deleted account data | 30 days, then purged |

Customers can request early deletion at any time per GDPR Article 17.
