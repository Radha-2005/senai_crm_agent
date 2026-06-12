# Escalation Matrix — SenAI CRM Internal Policy

## Overview
This document defines the escalation paths for different categories of customer issues. All team members must follow these protocols to ensure timely resolution and proper handling.

---

## 1. Legal Threats & Cease-and-Desist Letters
**Trigger:** Any email containing legal threats, lawsuits, attorney involvement, trademark/IP claims  
**Primary Owner:** Legal Team (legal@senai.io)  
**Secondary:** VP of Operations  
**Response SLA:** Acknowledge within 2 hours, legal review within 24 hours  
**Actions Required:**
- DO NOT respond substantively without legal approval
- Forward to legal@senai.io immediately with full email thread
- Create internal legal ticket tagged LEGAL-URGENT
- Log in compliance tracker

---

## 2. GDPR / Data Subject Requests
**Trigger:** GDPR Article 15 (access), Article 17 (erasure), Article 20 (portability), or any DPA inquiry  
**Primary Owner:** Data Protection Officer (dpo@senai.io)  
**Secondary:** Engineering (for data export)  
**Response SLA:** Acknowledge within 72 hours; fulfil within 30 days (statutory)  
**Actions Required:**
- Auto-acknowledge with reference to 30-day statutory window
- Create compliance ticket tagged GDPR-REQUEST
- Do NOT auto-reply with generic response
- Log request date for 30-day countdown
- Escalate to DPO immediately

---

## 3. Security Incidents (Ransomware / Data Breach / Suspicious Login)
**Trigger:** Any ransomware demand, data exfiltration claim, suspicious login from unusual IP  
**Primary Owner:** Security Team (security@senai.io)  
**Secondary:** CTO, Legal Team  
**Response SLA:** Immediate (within 15 minutes of detection)  
**Actions Required:**
- NEVER reply to the attacker/threat actor
- Escalate to security@senai.io and cto@senai.io immediately
- Initiate incident response protocol (IR-001)
- Preserve all evidence; do not delete any emails
- Notify legal if data breach is confirmed

---

## 4. P0 / Critical Outages (SLA Breach)
**Trigger:** Production down, >30 min downtime, SLA breach threshold crossed  
**Primary Owner:** DevOps On-Call  
**Secondary:** VP Engineering, Account Manager for affected customer  
**Response SLA:** Acknowledge within 15 minutes; RCA within 24 hours  
**Actions Required:**
- Create P0 incident ticket
- Notify DevOps on-call immediately
- Communicate proactively with affected customers
- Calculate SLA credit per formula (see sla_policy.md)
- Deliver RCA report within 24 hours for P0

---

## 5. VIP Churn Risk / High-Value Customer Complaints
**Trigger:** Customer with LTV >$10,000 threatens to cancel; 3+ unanswered emails; G2/Trustpilot threat  
**Primary Owner:** Customer Success Manager  
**Secondary:** VP Sales  
**Response SLA:** Respond within 1 hour; retention offer within 4 hours  
**Actions Required:**
- Immediate outreach from CSM (phone preferred)
- Check refund policy for retention credit offer (see refund_policy.md)
- Offer goodwill credit or account review
- Flag account for churn prevention workflow

---

## 6. PR / Media Inquiries
**Trigger:** Email from journalist, media outlet, investor, analyst  
**Primary Owner:** Marketing / PR team (pr@senai.io)  
**Secondary:** CEO for major publications  
**Response SLA:** Acknowledge within 2 hours; full response within 24 hours  
**Actions Required:**
- Do not make product claims without PR approval
- Forward to pr@senai.io immediately
- Gather context: publication name, deadline, topic

---

## 7. Enterprise RFP / Compliance Questionnaires
**Trigger:** Formal RFP, security questionnaire, compliance audit request  
**Primary Owner:** Solutions Engineer + Legal  
**Secondary:** CTO for technical sections  
**Response SLA:** Acknowledge within 4 hours; full response within 5 business days  
**Actions Required:**
- Assign to Solutions Engineer
- Legal reviews compliance sections
- Use approved answer library for SOC 2, HIPAA, GDPR questions (see compliance_faq.md)

---

## 8. Chatbot / AI Misinformation Complaints
**Trigger:** Customer claims AI chatbot gave incorrect information about pricing, refunds, or policies  
**Primary Owner:** Customer Success + Product  
**Secondary:** Legal (if customer is threatening legal action)  
**Response SLA:** Respond within 4 hours  
**Actions Required:**
- Retrieve actual policy from KB (do NOT rely on chatbot's claim)
- Acknowledge discrepancy empathetically (avoid admitting legal liability)
- Escalate to Product team for chatbot retraining
- Offer correct information per actual policy
- If customer threatens legal action, escalate to Legal
