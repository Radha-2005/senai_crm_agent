-- schema.sql - PostgreSQL database schema for SenAI CRM
-- Run this to create all tables manually if not using Alembic migrations

-- Enable UUID extension (optional)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Contacts table
CREATE TABLE IF NOT EXISTS contacts (
    id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    company VARCHAR(255),
    phone VARCHAR(50),
    tier VARCHAR(20) DEFAULT 'standard',
    ltv FLOAT DEFAULT 0.0,
    tags JSONB DEFAULT '[]',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);

-- Threads table
CREATE TABLE IF NOT EXISTS threads (
    id VARCHAR(50) PRIMARY KEY,
    contact_id VARCHAR(50) REFERENCES contacts(id),
    subject VARCHAR(500),
    status VARCHAR(30) DEFAULT 'open',
    last_agent_decision VARCHAR(50),
    sentiment_trend VARCHAR(20),
    priority_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_threads_contact_id ON threads(contact_id);
CREATE INDEX IF NOT EXISTS idx_threads_status ON threads(status);

-- Emails table
CREATE TABLE IF NOT EXISTS emails (
    id VARCHAR(50) PRIMARY KEY,
    thread_id VARCHAR(50) REFERENCES threads(id),
    contact_id VARCHAR(50) REFERENCES contacts(id),
    subject VARCHAR(500),
    body TEXT,
    sender_email VARCHAR(255),
    received_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'pending',
    classification VARCHAR(100),
    sentiment VARCHAR(20),
    confidence FLOAT,
    agent_decision VARCHAR(50),
    agent_steps JSONB,
    draft_reply TEXT,
    draft_approved BOOLEAN DEFAULT FALSE,
    raw_payload JSONB,
    ingested_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emails_thread_id ON emails(thread_id);
CREATE INDEX IF NOT EXISTS idx_emails_contact_id ON emails(contact_id);
CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails(received_at);
CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(status);

-- Processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id SERIAL PRIMARY KEY,
    email_id VARCHAR(50) REFERENCES emails(id),
    status VARCHAR(20) DEFAULT 'queued',
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_processing_jobs_email_id ON processing_jobs(email_id);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    email_id VARCHAR(50),
    thread_id VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    actor VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_email_id ON audit_logs(email_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_thread_id ON audit_logs(thread_id);
