"""
Database Migration: Vectorstore Refactoring

This migration:
1. Adds user_id column to documents table
2. Adds is_embedded and embedded_at columns to documents
3. Creates user_vectorstores table
4. Populates user_id from existing project ownership
5. Clears old embedding data
6. Drops old embedding_versions and version_documents tables

Run with: psql -U user -d otis -f migration.sql
"""

-- ============================================================================
-- STEP 1: Add new columns to documents table
-- ============================================================================

-- Add user_id column (nullable first, we'll populate then make NOT NULL)
ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(user_id) ON DELETE CASCADE;

-- Add embedding status tracking columns
ALTER TABLE documents ADD COLUMN IF NOT EXISTS is_embedded BOOLEAN DEFAULT FALSE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS embedded_at TIMESTAMP;

-- ============================================================================
-- STEP 2: Populate user_id from existing project ownership
-- ============================================================================

-- For each document, set user_id to the owner of any project it's linked to
-- (If a doc is in multiple projects by different users, this takes the first one)
UPDATE documents d
SET user_id = (
    SELECT p.created_by
    FROM project_docs pd
    JOIN projects p ON pd.project_id = p.project_id
    WHERE pd.doc_id = d.doc_id
    LIMIT 1
)
WHERE d.user_id IS NULL;

-- For any orphaned documents (not in any project), we need to handle them
-- Option A: Delete them
-- DELETE FROM documents WHERE user_id IS NULL;

-- Option B: Assign to a default admin user (uncomment and set admin user_id)
-- UPDATE documents SET user_id = 'YOUR_ADMIN_USER_ID' WHERE user_id IS NULL;

-- ============================================================================
-- STEP 3: Create user_vectorstores table
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_vectorstores (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    collection_id UUID REFERENCES langchain_pg_collection(uuid) ON DELETE SET NULL,
    document_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    job_id VARCHAR(100),
    error_message TEXT,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

-- ============================================================================
-- STEP 4: Clear old embedding data
-- ============================================================================

-- Delete all embeddings
DELETE FROM langchain_pg_embedding;

-- Delete all collections that were project-based
DELETE FROM langchain_pg_collection WHERE name LIKE 'project_%';

-- ============================================================================
-- STEP 5: Drop old tables (AFTER clearing embeddings to avoid FK issues)
-- ============================================================================

-- Drop version_documents first (has FK to embedding_versions)
DROP TABLE IF EXISTS version_documents CASCADE;

-- Drop embedding_versions
DROP TABLE IF EXISTS embedding_versions CASCADE;

-- ============================================================================
-- STEP 6: Make user_id NOT NULL (after populating)
-- ============================================================================

-- Only run this if all documents have a user_id assigned
-- Check first: SELECT COUNT(*) FROM documents WHERE user_id IS NULL;
-- If count is 0, run:
-- ALTER TABLE documents ALTER COLUMN user_id SET NOT NULL;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check documents have user_id:
-- SELECT COUNT(*) as total, COUNT(user_id) as with_user FROM documents;

-- Check new table created:
-- SELECT * FROM user_vectorstores;

-- Check old tables dropped:
-- SELECT table_name FROM information_schema.tables WHERE table_name IN ('embedding_versions', 'version_documents');
