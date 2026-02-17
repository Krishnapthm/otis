from typing import List, Optional
import uuid
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Concept(BaseModel):
    name: str = Field(description="Concept Name")
    summary: str = Field(description="Concept Summary")
    # search_queries: List[str] = Field(description="search queries")


class SearchQueries(BaseModel):
    queries: List[str] = Field(default_factory=list)


class Overview(BaseModel):
    """
    Overview of the document
    """

    doc_name: str = Field(description="Document Name")
    concepts: List[Concept]


class DocumentContent(BaseModel):
    doc_id: uuid.UUID
    content_md: str


class AgentState(TypedDict, total=False):
    """
    Agent State
    """

    doc_ids: List[uuid.UUID]
    collection_name: Optional[List[str]] = None
    documents: Optional[List[DocumentContent]] = None
    overview: Optional[List[Overview]] = None
    user_prompt: Optional[List[str]] = None
    retrived_context: List
    selected_concepts: List[Concept]
    search_queries: List[SearchQueries]
