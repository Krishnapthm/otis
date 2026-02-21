"""
Backfill file_hash for existing documents.

Memory-safe: uses yield_per() to stream records in batches.
Run once after migration: python -m scripts.backfill_file_hashes

Usage:
    cd /home/krishna/projects/otis
    python -m scripts.backfill_file_hashes
"""

import os
import hashlib
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.api.db.models import Documents
from src.core.hashing import compute_file_hash_streaming

BATCH_SIZE = 100
PLACEHOLDER = "PENDING_BACKFILL"


def backfill():
    """
    Backfill file_hash for documents marked with PENDING_BACKFILL placeholder.
    
    Memory-safe: streams records in batches of 100.
    """
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/otis")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return
    
    # Convert async URL to sync if needed
    sync_db_url = db_url.replace("+asyncpg", "").replace("+psycopg", "")
    
    engine = create_engine(sync_db_url)
    
    with Session(engine) as db:
        # Count total documents needing backfill
        count_result = db.execute(
            text(f"SELECT COUNT(*) FROM documents WHERE file_hash = '{PLACEHOLDER}'")
        )
        total = count_result.scalar()
        print(f"Found {total} documents needing file_hash backfill")
        
        if total == 0:
            print("Nothing to backfill. Exiting.")
            return
        
        # Stream records in batches using yield_per
        query = db.query(Documents).filter(Documents.file_hash == PLACEHOLDER)
        
        processed = 0
        errors = 0
        
        for doc in query.yield_per(BATCH_SIZE):
            try:
                if os.path.exists(doc.file_path):
                    # File exists - compute hash from file
                    doc.file_hash = compute_file_hash_streaming(doc.file_path)
                elif doc.content_md:
                    # File missing but content exists - hash content as fallback
                    doc.file_hash = hashlib.sha256(doc.content_md.encode()).hexdigest()
                else:
                    # No file, no content - generate unique hash from doc_id
                    doc.file_hash = hashlib.sha256(str(doc.doc_id).encode()).hexdigest()
                    print(f"  WARNING: Doc {doc.doc_id} has no file or content, using doc_id hash")
                
                processed += 1
                
                # Commit in batches
                if processed % BATCH_SIZE == 0:
                    db.commit()
                    print(f"  Processed {processed}/{total} documents...")
                    
            except Exception as e:
                errors += 1
                print(f"  ERROR processing doc {doc.doc_id}: {e}")
        
        # Final commit
        db.commit()
        
        print(f"\nBackfill complete:")
        print(f"  - Processed: {processed}")
        print(f"  - Errors: {errors}")
        print(f"\nNext steps:")
        print(f"  1. Verify: SELECT COUNT(*) FROM documents WHERE file_hash = '{PLACEHOLDER}';")
        print(f"  2. If 0, run: ALTER TABLE documents ALTER COLUMN file_hash SET NOT NULL;")


if __name__ == "__main__":
    backfill()
