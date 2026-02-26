"""Service for fetching concept-map data from the database."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from sqlalchemy import text as sa_text

from src.api.db.models.session import async_session_maker


async def fetch_concept_map(doc_ids: List[uuid.UUID]) -> List[Dict[str, Any]]:
    """Return concept rows for the given document IDs."""
    if not doc_ids:
        return []

    query = sa_text(
        """
        SELECT document_id, concept_name, concept_summary
        FROM document_concepts
        WHERE document_id = ANY(:doc_ids)
        ORDER BY document_id, concept_name
        """
    )

    async with async_session_maker() as db:
        result = await db.execute(
            query, {"doc_ids": [str(doc_id) for doc_id in doc_ids]}
        )
        rows = result.fetchall()

    return [
        {
            "doc_id": str(row.document_id),
            "name": row.concept_name,
            "summary": row.concept_summary,
        }
        for row in rows
    ]
