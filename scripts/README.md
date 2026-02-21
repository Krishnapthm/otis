# Otis Scripts

Utility scripts for database operations and maintenance.

## backfill_file_hashes.py

Backfills `file_hash` column for existing documents after migration.

```bash
# Run from project root with DATABASE_URL set
cd /home/krishna/projects/otis
source .env  # or export DATABASE_URL=...
python -m scripts.backfill_file_hashes
```

## Post-Backfill Steps

After successful backfill, enforce NOT NULL constraint:

```sql
ALTER TABLE documents ALTER COLUMN file_hash SET NOT NULL;
```
