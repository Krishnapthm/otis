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
    user_prompt: Optional[str] = None
    # collection_id is now derived from user's vectorstore, not passed


class Concept(BaseModel):
    name: str = Field(description="Concept Name")
    summary: str = Field(description="Concept Summary")


class DocumentConceptResponse(BaseModel):
    """Response schema for a pre-extracted document concept."""

    concept_id: UUID4
    document_id: UUID4
    concept_name: str
    concept_summary: str
    extractor_version: str = "v1"
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ConceptMatchResult(BaseModel):
    """Result from Layer-1 concept matching during retrieval."""

    concept_name: str
    concept_summary: str
    score: float = Field(description="Cosine similarity score (0-1)")


class ResumeRequest(BaseModel):
    selected_concepts: List[Concept]


# ============================================================================
# Chat Schemas
# ============================================================================


class ChatCreate(BaseModel):
    title: Optional[str] = None


class ChatUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[Literal["active", "archived", "deleted"]] = None


class ChatResponse(BaseModel):
    chat_id: UUID4
    user_id: UUID4
    status: Literal["active", "archived", "deleted"]
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    title: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_message_at: Optional[datetime.datetime] = None
    deleted_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    role: Literal["user", "assistant", "tool"]
    content: Optional[str] = None
    structured_data: Optional[dict] = None
    doc_ids: Optional[List[uuid.UUID]] = None
    status: Literal["pending", "streaming", "completed", "failed"] = "completed"
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    error: Optional[dict] = None


class ChatMessageUpdate(BaseModel):
    content: Optional[str] = None
    structured_data: Optional[dict] = None
    doc_ids: Optional[List[uuid.UUID]] = None
    status: Optional[Literal["pending", "streaming", "completed", "failed"]] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    error: Optional[dict] = None


class ChatMessageResponse(BaseModel):
    message_id: UUID4
    chat_id: UUID4
    role: Literal["user", "assistant", "tool"]
    sequence: int
    status: Literal["pending", "streaming", "completed", "failed"]
    content: Optional[str] = None
    structured_data: Optional[dict] = None
    doc_ids: List[UUID4] = Field(default_factory=list)
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    error: Optional[dict] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# ── Message Event Schemas ────────────────────────────────────────────────────


class ChatMessageEventResponse(BaseModel):
    """Single persisted streaming event."""

    event_id: UUID4
    message_id: UUID4
    seq: int
    event_type: str
    content: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ChatMessageEventReplayResponse(BaseModel):
    """Batch of events for replay, with completion flag."""

    events: List[ChatMessageEventResponse]
    is_complete: bool = Field(
        description="True when the parent message has reached a terminal state (completed/failed)"
    )
    last_seq: int = Field(
        description="Highest seq returned; client passes this as after_seq to resume"
    )


# ── Invoke / Streaming ──────────────────────────────────────────────────────


class ChatInvokeRequest(BaseModel):
    message: str
    doc_ids: Optional[List[uuid.UUID]] = None
    mentions: Optional[List[dict]] = None
    edit_mode: bool = False
    edit_target: Literal["all", "specific"] = "all"
    edit_indices: List[int] = Field(default_factory=list)
    edit_strategy: Literal["regenerate", "patch"] = "regenerate"
