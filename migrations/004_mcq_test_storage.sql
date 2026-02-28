-- Migration: 004_mcq_test_storage
-- Description: Extend mcqs table for MCQTest structured storage
-- Date: 2026-02-28

ALTER TABLE mcqs
    ADD COLUMN IF NOT EXISTS test_id UUID,
    ADD COLUMN IF NOT EXISTS doc_ids UUID[],
    ADD COLUMN IF NOT EXISTS plan JSONB,
    ADD COLUMN IF NOT EXISTS questions JSONB,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now(),
    ADD COLUMN IF NOT EXISTS test_name TEXT;

-- Backfill created_at from legacy generated_at where available
UPDATE mcqs
SET created_at = generated_at
WHERE created_at IS NULL AND generated_at IS NOT NULL;

-- Backfill test_id and test_name defaults for existing rows
UPDATE mcqs
SET
    test_id = COALESCE(test_id, gen_random_uuid()),
    test_name = COALESCE(NULLIF(test_name, ''), 'Untitled MCQ Test')
WHERE test_id IS NULL OR test_name IS NULL OR test_name = '';
