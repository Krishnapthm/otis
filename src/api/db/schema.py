import string
import uuid
from pydantic import BaseModel, UUID4, Field, field_validator
from typing import List, Literal, Optional
import datetime


# ============================================================================
# MCQ Schemas
# ============================================================================

class Options(BaseModel):
    id: Literal["A", "B", "C", "D"] = Field(description="Option id")
    text: str = Field(description="Options for the answer of MCQ")


class Questions(BaseModel):
    question_id: int = Field(description="The unique id of the MCQ")
    question: str = Field(description="Generated Question")
    options: List[Options] = Field(
        description="The list of options for the generated MCQ"
    )
    answer: Literal["A", "B", "C", "D"] = Field(
        description="The correct option for the MCQ"
    )
    explanation: str = Field(description="Explanation for the right answer")


class MCQ(BaseModel):
    questions: List[Questions] = Field(description="Multiple Choice Questions")


class CreateMCQ(BaseModel):
    mcq: MCQ


class ReadMCQ(CreateMCQ):
    mcq_id: UUID4
    generated_at: datetime.datetime


# ============================================================================
# Document Schemas
# ============================================================================

class DocBase(BaseModel):
    filename: str
    file_type: str
    file_size: int
    file_path: str
    file_hash: Optional[str] = None  # SHA-256 of raw file bytes


class DocResponse(DocBase):
    doc_id: UUID4
    user_id: UUID4
    project_id: Optional[UUID4] = None  # Optional now since docs belong to users
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None
    is_embedded: bool = False
    embedded_at: datetime.datetime | None = None
    status: Literal["pending", "processing", "ready", "failed"] = "pending"
    canonical_document_id: Optional[UUID4] = None


class DocDelete(BaseModel):
    doc_id: List[uuid.UUID]


class DocLinkRequest(BaseModel):
    """Request to link existing documents to a project"""
    doc_ids: List[uuid.UUID]


class Metadata(BaseModel):
    source: str
    file_name: str


# ============================================================================
# Vectorstore/Embedding Schemas (Simplified - One per User)
# ============================================================================

class VectorstoreStatus(BaseModel):
    """Status of a user's vectorstore"""
    user_id: UUID4
    collection_id: Optional[UUID4] = None
    status: Literal["pending", "processing", "ready", "failed"]
    total_documents: int = Field(description="Total documents owned by user")
    embedded_documents: int = Field(description="Documents that are embedded")
    pending_documents: int = Field(description="Documents waiting to be embedded")
    last_synced_at: Optional[datetime.datetime] = None
    error_message: Optional[str] = None


class VectorstoreSyncRequest(BaseModel):
    """Optional: specify which documents to sync (if empty, sync all pending)"""
    doc_ids: Optional[List[uuid.UUID]] = None


class VectorstoreSyncResponse(BaseModel):
    """Response after initiating sync"""
    status: str
    message: str
    documents_queued: int
    job_id: Optional[str] = None


class EmbeddingResponse(Metadata):
    page_content: str


# ============================================================================
# Project Schemas
# ============================================================================

class ProjectBase(BaseModel):
    project_name: str
    project_desc: Optional[str] = None


class ProjectResponse(ProjectBase):
    project_id: UUID4
    created_at: datetime.datetime
    created_by: UUID4


# ============================================================================
# User/Auth Schemas
# ============================================================================

class CreateUser(BaseModel):
    email: str
    uname: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in string.punctuation for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginUser(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user_id: UUID4
    uname: str
    email: str
    role: Literal["admin", "user"]


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID4
    uname: str
    email: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Agent/Graph Schemas
# ============================================================================

class ChunkDocuments(BaseModel):
    doc_name: str
    chunk_count: int


class StartGraphRequest(BaseModel):
    """Updated: Uses user's collection instead of project-specific collection"""
    doc_ids: List[uuid.UUID]
    # collection_id is now derived from user's vectorstore, not passed


class Concept(BaseModel):
    name: str = Field(description="Concept Name")
    summary: str = Field(description="Concept Summary")


class ResumeRequest(BaseModel):
    selected_concepts: List[Concept]
