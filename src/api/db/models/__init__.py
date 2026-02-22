from typing import Any, List, Optional

from pgvector.sqlalchemy.vector import VECTOR
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import uuid


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", name="users_pkey"),
        UniqueConstraint("email", name="users_email_key"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(Text)
    hashed_password: Mapped[str] = mapped_column(Text)
    user_name: Mapped[str] = mapped_column("uname", String)
    role: Mapped[str] = mapped_column(Text, server_default=text("'user'::text"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, server_default=text("now()")
    )
    is_active: Mapped[Optional[bool]] = mapped_column(
        Boolean, server_default=text("true")
    )

    # New relationships
    documents: Mapped[List["Documents"]] = relationship(
        "Documents", back_populates="owner"
    )
    vectorstore: Mapped[Optional["UserVectorstore"]] = relationship(
        "UserVectorstore", back_populates="user", uselist=False
    )


class Documents(Base):
    __tablename__ = "documents"
    __table_args__ = (PrimaryKeyConstraint("doc_id", name="documents_pkey"),)

    doc_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    # Document belongs to a user
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String)
    file_type: Mapped[str] = mapped_column(String)
    file_size: Mapped[int] = mapped_column(Integer)
    file_path: Mapped[str] = mapped_column(String)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    content_md: Mapped[Optional[str]] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    
    # Deduplication fields
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA-256 of raw file
    status: Mapped[str] = mapped_column(
        String(20), server_default=text("'pending'")
    )  # pending | processing | ready | failed
    canonical_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("documents.doc_id", ondelete="SET NULL"), nullable=True
    )  # Links to canonical doc with same content_hash
    
    # Track embedding status (idempotency)
    is_embedded: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    embedded_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    # Relationships
    owner: Mapped["Users"] = relationship("Users", back_populates="documents")
    project: Mapped[List["Projects"]] = relationship(
        "Projects", secondary="project_docs", back_populates="doc"
    )



class LangchainPgCollection(Base):
    __tablename__ = "langchain_pg_collection"
    __table_args__ = (
        PrimaryKeyConstraint("uuid", name="langchain_pg_collection_pkey"),
        UniqueConstraint("name", name="langchain_pg_collection_name_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column("uuid", Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    cmetadata: Mapped[Optional[dict]] = mapped_column(JSON)

    # Updated relationship - now links to UserVectorstore
    user_vectorstore: Mapped[Optional["UserVectorstore"]] = relationship(
        "UserVectorstore", back_populates="collection", uselist=False
    )
    langchain_pg_embedding: Mapped[List["LangchainPgEmbedding"]] = relationship(
        "LangchainPgEmbedding", back_populates="collection"
    )


class UserVectorstore(Base):
    """
    One vectorstore per user. Stores the user's single embedding collection.
    Replaces the old EmbeddingVersions model.
    """
    __tablename__ = "user_vectorstores"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", name="user_vectorstores_pkey"),
        ForeignKeyConstraint(
            ["collection_id"],
            ["langchain_pg_collection.uuid"],
            ondelete="SET NULL",
            name="user_vectorstores_collection_id_fkey",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    collection_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    document_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    status: Mapped[str] = mapped_column(
        String(50), server_default=text("'pending'::character varying")
    )
    job_id: Mapped[Optional[str]] = mapped_column(String(100))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    last_synced_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, server_default=text("now()")
    )

    # Relationships
    user: Mapped["Users"] = relationship("Users", back_populates="vectorstore")
    collection: Mapped[Optional["LangchainPgCollection"]] = relationship(
        "LangchainPgCollection", back_populates="user_vectorstore"
    )


class Mcqs(Base):
    __tablename__ = "mcqs"
    __table_args__ = (PrimaryKeyConstraint("mcq_id", name="mcqs_pkey"),)

    mcq_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    generated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    mcq: Mapped[Optional[dict]] = mapped_column(JSONB)

    project: Mapped[List["Projects"]] = relationship(
        "Projects", secondary="project_mcqs", back_populates="mcq"
    )


class Projects(Base):
    __tablename__ = "projects"
    __table_args__ = (PrimaryKeyConstraint("project_id", name="projects_pkey"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_name: Mapped[str] = mapped_column(String)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid)
    project_desc: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, server_default=text("now()")
    )

    doc: Mapped[List["Documents"]] = relationship(
        "Documents", secondary="project_docs", back_populates="project"
    )
    mcq: Mapped[List["Mcqs"]] = relationship(
        "Mcqs", secondary="project_mcqs", back_populates="project"
    )


class Chats(Base):
    __tablename__ = "chats"
    __table_args__ = (
        CheckConstraint(
            "status = ANY (ARRAY['active'::text, 'archived'::text, 'deleted'::text])",
            name="chats_status_check",
        ),
        ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name="chats_user_id_fkey",
        ),
        PrimaryKeyConstraint("chat_id", name="chats_pkey"),
        Index("idx_chats_last_message_at", "last_message_at"),
        Index("idx_chats_status", "status"),
        Index("idx_chats_user_id", "user_id"),
    )

    chat_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(Text, server_default=text("'active'::text"))
    total_input_tokens: Mapped[int] = mapped_column(
        Integer, server_default=text("0")
    )
    total_output_tokens: Mapped[int] = mapped_column(
        Integer, server_default=text("0")
    )
    title: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    last_message_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True)
    )


class ChatMessages(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        CheckConstraint(
            "role = ANY (ARRAY['user'::text, 'assistant'::text, 'tool'::text])",
            name="chat_messages_role_check",
        ),
        CheckConstraint(
            "status = ANY (ARRAY['pending'::text, 'streaming'::text, 'completed'::text, 'failed'::text])",
            name="chat_messages_status_check",
        ),
        ForeignKeyConstraint(
            ["chat_id"],
            ["chats.chat_id"],
            ondelete="CASCADE",
            name="chat_messages_chat_id_fkey",
        ),
        PrimaryKeyConstraint("message_id", name="chat_messages_pkey"),
        Index("idx_messages_chat_id", "chat_id"),
        Index("idx_messages_chat_sequence", "chat_id", "sequence"),
    )

    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    role: Mapped[str] = mapped_column(Text)
    sequence: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(Text, server_default=text("'completed'::text"))
    content: Mapped[Optional[str]] = mapped_column(Text)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    error: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )


class LangchainPgEmbedding(Base):
    __tablename__ = "langchain_pg_embedding"
    __table_args__ = (
        ForeignKeyConstraint(
            ["collection_id"],
            ["langchain_pg_collection.uuid"],
            ondelete="CASCADE",
            name="langchain_pg_embedding_collection_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="langchain_pg_embedding_pkey"),
        Index("ix_cmetadata_gin", "cmetadata"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    collection_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    embedding: Mapped[Optional[Any]] = mapped_column(VECTOR)
    document: Mapped[Optional[str]] = mapped_column(String)
    cmetadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    collection: Mapped[Optional["LangchainPgCollection"]] = relationship(
        "LangchainPgCollection", back_populates="langchain_pg_embedding"
    )


# Junction table: Projects <-> Documents (many-to-many)
t_project_docs = Table(
    "project_docs",
    Base.metadata,
    Column("project_id", Uuid, primary_key=True, nullable=False),
    Column("doc_id", Uuid, primary_key=True, nullable=False),
    ForeignKeyConstraint(
        ["doc_id"],
        ["documents.doc_id"],
        ondelete="CASCADE",
        name="project_docs_doc_id_fkey",
    ),
    ForeignKeyConstraint(
        ["project_id"],
        ["projects.project_id"],
        ondelete="CASCADE",
        name="project_docs_project_id_fkey",
    ),
    PrimaryKeyConstraint("project_id", "doc_id", name="project_docs_pkey"),
)


# Junction table: Projects <-> MCQs (many-to-many)
t_project_mcqs = Table(
    "project_mcqs",
    Base.metadata,
    Column("project_id", Uuid, primary_key=True, nullable=False),
    Column("mcq_id", Uuid, primary_key=True, nullable=False),
    ForeignKeyConstraint(
        ["mcq_id"], ["mcqs.mcq_id"], ondelete="CASCADE", name="project_mcqs_mcq_id_fkey"
    ),
    ForeignKeyConstraint(
        ["project_id"],
        ["projects.project_id"],
        ondelete="CASCADE",
        name="project_mcqs_project_id_fkey",
    ),
    PrimaryKeyConstraint("project_id", "mcq_id", name="project_mcqs_pkey"),
)


class ConceptCache(Base):
    """
    Cache for concept extraction results.
    
    Prevents redundant LLM calls for documents with identical content.
    Keyed by (content_hash, extractor_version) with 90-day TTL.
    """
    __tablename__ = "concept_cache"
    __table_args__ = (
        UniqueConstraint("content_hash", "extractor_version", name="uq_concept_cache"),
    )

    cache_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(50), nullable=False)
    concepts: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=text("now()")
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=text("now() + interval '90 days'")
    )


class MCQCache(Base):
    """
    Cache for MCQ generation results.
    
    Prevents redundant LLM calls for identical concept sets with same parameters.
    Keyed by (concept_set_id, generator_version, params_hash) with 90-day TTL.
    """
    __tablename__ = "mcq_cache"
    __table_args__ = (
        UniqueConstraint(
            "concept_set_id", "generator_version", "params_hash", name="uq_mcq_cache"
        ),
    )

    cache_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    concept_set_id: Mapped[str] = mapped_column(String(64), nullable=False)
    generator_version: Mapped[str] = mapped_column(String(50), nullable=False)
    params_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    mcqs: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=text("now()")
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=text("now() + interval '90 days'")
    )

