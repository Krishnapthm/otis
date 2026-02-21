-- =====================================================
-- PDF Ingestion Pipeline - Lean Dedup Migration
-- =====================================================
-- Run with: psql -U user -d otis -f migrations/add_dedup_lean.sql

-- 0. Enable required extension for SHA-256 function
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================================
-- 1. Add deduplication columns to documents
-- =====================================================
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ready';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS canonical_document_id UUID REFERENCES documents(doc_id) ON DELETE SET NULL;

-- =====================================================
-- 2. Backfill existing documents
-- =====================================================
-- Mark all existing docs as 'ready' (they're already processed)
UPDATE documents SET status = 'ready' WHERE status IS NULL;

-- Set placeholder for existing documents (to be updated by Python backfill script)
-- Using a clear marker that the Python script will match on
UPDATE documents SET file_hash = 'PENDING_BACKFILL'
WHERE file_hash IS NULL;

-- =====================================================
-- 3. Create indexes for deduplication lookups
-- =====================================================
-- Partial unique index: enforces uniqueness only for non-NULL file_hash
-- This allows legacy NULL records but prevents duplicates for new uploads
CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_user_file_hash 
ON documents(user_id, file_hash) 
WHERE file_hash IS NOT NULL AND file_hash != 'PENDING_BACKFILL';

-- Index for content_hash lookups (not unique - multiple files can have same content)
CREATE INDEX IF NOT EXISTS idx_documents_user_content_hash 
ON documents(user_id, content_hash) 
WHERE content_hash IS NOT NULL;

-- =====================================================
-- 4. Post-Backfill Steps (run AFTER Python backfill completes)
-- =====================================================
-- Uncomment and run these after running scripts/backfill_file_hashes.py:
--
-- DROP INDEX IF EXISTS idx_documents_user_file_hash;
-- CREATE UNIQUE INDEX idx_documents_user_file_hash 
--     ON documents(user_id, file_hash) 
--     WHERE file_hash IS NOT NULL;
-- ALTER TABLE documents ALTER COLUMN file_hash SET NOT NULL;

-- =====================================================
-- Concept Cache Table
-- =====================================================
CREATE TABLE IF NOT EXISTS concept_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_hash VARCHAR(64) NOT NULL,
    extractor_version VARCHAR(50) NOT NULL,
    concepts JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '90 days',
    UNIQUE(content_hash, extractor_version)
);

CREATE INDEX IF NOT EXISTS idx_concept_cache_lookup 
ON concept_cache(content_hash, extractor_version);

CREATE INDEX IF NOT EXISTS idx_concept_cache_expires 
ON concept_cache(expires_at);

-- =====================================================
-- MCQ Cache Table
-- =====================================================
CREATE TABLE IF NOT EXISTS mcq_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_set_id VARCHAR(64) NOT NULL,
    generator_version VARCHAR(50) NOT NULL,
    params_hash VARCHAR(64) NOT NULL,
    mcqs JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '90 days',
    UNIQUE(concept_set_id, generator_version, params_hash)
);

CREATE INDEX IF NOT EXISTS idx_mcq_cache_lookup 
ON mcq_cache(concept_set_id, generator_version, params_hash);

CREATE INDEX IF NOT EXISTS idx_mcq_cache_expires 
ON mcq_cache(expires_at);

-- =====================================================
-- Cleanup function for expired cache entries
-- =====================================================
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM concept_cache WHERE expires_at < NOW();
    DELETE FROM mcq_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Optional: Schedule cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-cache', '0 3 * * *', 'SELECT cleanup_expired_cache()');
