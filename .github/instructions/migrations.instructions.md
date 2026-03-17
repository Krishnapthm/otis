---
applyTo: "migrations/**"
---

# Database Migrations — canonical patterns

> These rules apply to every file under `migrations/`. They complement the
> cross-cutting rules in `.github/copilot-instructions.md`.

## File naming

```
NNN_descriptive_name.sql
```

- `NNN` — 3-digit zero-padded integer, strictly sequential (`001`, `002`, ...)
- `descriptive_name` — snake_case, describes what the migration does
- Example: `005_add_user_preferences.sql`

Never create a migration without a numeric prefix. `add_dedup_lean.sql`
violates this rule — rename to `000_add_dedup_lean.sql` on next touch.

## Required header

Every migration file must begin with this block:

```sql
-- Migration: NNN_descriptive_name
-- Date:      YYYY-MM-DD
-- Description: One-line plain-English summary of what this migration does.
```

## Transaction wrapping

Every migration must be wrapped in a transaction so it is atomic — either
fully applied or fully rolled back on error.

```sql
-- Migration: 005_add_user_preferences
-- Date:      2026-03-04
-- Description: Add per-user preference JSON column to the users table.

BEGIN;

ALTER TABLE users ADD COLUMN preferences JSONB NOT NULL DEFAULT '{}';

COMMIT;
```

## SQL style

- **Keywords**: `UPPERCASE` (`CREATE TABLE`, `ALTER TABLE`, `INSERT INTO`, `SELECT`)
- **Identifiers**: `lowercase_snake_case` (table names, column names, indexes)
- **Timestamps**: Always `TIMESTAMPTZ NOT NULL DEFAULT now()` — never bare
  `TIMESTAMP` (which is timezone-naive)
- **Primary keys**: `UUID DEFAULT gen_random_uuid()`
- **Constraint naming**:
  - Unique: `uq_table_column`
  - Index: `idx_table_column`
  - Foreign key: `fk_table_referenced_table`

```sql
-- ✅ correct
CREATE TABLE document_chunks (
    id          UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID        NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content     TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);

-- ❌ wrong
create table document_chunks (
    id uuid primary key,
    created_at TIMESTAMP  -- timezone-naive!
);
```

## Foreign keys

- `ON DELETE CASCADE` for ownership relationships (a chunk belongs to a document)
- `ON DELETE SET NULL` for optional/soft references

## On-touch cleanup checklist

When you edit **any** file in `migrations/`, also fix these in that same file:

- [ ] Add `BEGIN;` / `COMMIT;` if the migration is not already wrapped in a transaction
- [ ] Normalize `TIMESTAMP` → `TIMESTAMPTZ NOT NULL` on any columns you touch
- [ ] Add the required header comment block if it is missing
- [ ] `add_dedup_lean.sql` → rename to `000_add_dedup_lean.sql` (the file has
      no numeric prefix, breaking the naming convention)
- [ ] Remove any Python-style `"""` docstring wrapping from SQL files
      (`migrations/001_vectorstore_refactor.sql` has invalid triple-quoted SQL)
