-- Migration: 002_document_concepts
-- Creates the document_concepts table for storing pre-extracted concepts
-- with their vector embeddings, enabling two-layer retrieval.
--
-- Depends on: pgvector extension (already enabled), documents table
-- Related: concept_cache table (existing, for content-hash-based dedup)

BEGIN;

-- Concept index: one row per concept per document
CREATE TABLE IF NOT EXISTS document_concepts (
    concept_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL
                        REFERENCES documents(doc_id) ON DELETE CASCADE,
    concept_name    TEXT NOT NULL,
    concept_summary TEXT NOT NULL,

    -- Embedding of the concept summary, used for Layer-1 retrieval.
    -- 768 dims = nomic-embed-text (current model).
    -- If the embedding model changes, ALTER this column and re-embed.
    concept_embedding VECTOR(768),

    extractor_version TEXT NOT NULL DEFAULT 'v1',
    created_at      TIMESTAMP NOT NULL DEFAULT now(),

    -- Prevent duplicate concepts for the same document
    CONSTRAINT uq_document_concept UNIQUE (document_id, concept_name)
);

-- Fast lookup by document
CREATE INDEX IF NOT EXISTS idx_document_concepts_doc_id
    ON document_concepts (document_id);

-- ANN index for cosine similarity search on concept embeddings
CREATE INDEX IF NOT EXISTS idx_document_concepts_embedding
    ON document_concepts
    USING ivfflat (concept_embedding vector_cosine_ops)
    WITH (lists = 100);

COMMIT;
