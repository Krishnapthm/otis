import uuid
from fastapi import Depends
import httpx
from typing import List, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from pydantic import UUID4

from src.api.db.models import Documents
from src.api.db.models.session import get_db
from src.agents.utils.state import DocumentContent


async def fetch_document_content(
    doc_ids: List[UUID4], db: AsyncSession
) -> List[DocumentContent]:

    docs = (
        await db.execute(select(Documents).where(Documents.doc_id.in_(doc_ids)))
    ).scalars()

    return [DocumentContent(doc_id=d.doc_id, content_md=d.content_md) for d in docs]


class DocumentService:

    def __init__(self, api_base: str):
        self.api_base = api_base
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_documents(
        self,
        doc_ids: List[uuid.UUID],
    ) -> List[DocumentContent]:

        response = await self.client.post(
            self.api_base,
            json={"doc_ids": [str(doc_id) for doc_id in doc_ids]},
        )

        response.raise_for_status()
        data = response.json()
        return data["documents"]

    async def close(self):
        await self.client.aclose()
