from typing import Any, List, Optional

from pgvector.sqlalchemy.vector import VECTOR
from sqlalchemy import Boolean, Column, DateTime, ForeignKeyConstraint, Index, Integer, JSON, PrimaryKeyConstraint, String, Table, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import uuid

class Base(DeclarativeBase):
    pass


class Documents(Base):
    __tablename__ = 'documents'
    __table_args__ = (
        PrimaryKeyConstraint('doc_id', name='documents_pkey'),
    )

    doc_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    filename: Mapped[str] = mapped_column(String)
    file_type: Mapped[str] = mapped_column(String)
    file_size: Mapped[int] = mapped_column(Integer)
    file_path: Mapped[str] = mapped_column(String)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    project: Mapped[List['Projects']] = relationship('Projects', secondary='project_docs', back_populates='doc')
    version_documents: Mapped[List['VersionDocuments']] = relationship('VersionDocuments', back_populates='document')


class LangchainPgCollection(Base):
    __tablename__ = 'langchain_pg_collection'
    __table_args__ = (
        PrimaryKeyConstraint('uuid', name='langchain_pg_collection_pkey'),
        UniqueConstraint('name', name='langchain_pg_collection_name_key')
    )

    id: Mapped[uuid.UUID] = mapped_column("uuid", Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    cmetadata: Mapped[Optional[dict]] = mapped_column(JSON)

    embedding_versions: Mapped['EmbeddingVersions'] = relationship('EmbeddingVersions', uselist=False, back_populates='collection')
    langchain_pg_embedding: Mapped[List['LangchainPgEmbedding']] = relationship('LangchainPgEmbedding', back_populates='collection')


class Mcqs(Base):
    __tablename__ = 'mcqs'
    __table_args__ = (
        PrimaryKeyConstraint('mcq_id', name='mcqs_pkey'),
    )

    mcq_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    generated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    mcq: Mapped[Optional[dict]] = mapped_column(JSONB)

    project: Mapped[List['Projects']] = relationship('Projects', secondary='project_mcqs', back_populates='mcq')


class Projects(Base):
    __tablename__ = 'projects'
    __table_args__ = (
        PrimaryKeyConstraint('project_id', name='projects_pkey'),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    project_name: Mapped[str] = mapped_column(String)
    project_desc: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    doc: Mapped[List['Documents']] = relationship('Documents', secondary='project_docs', back_populates='project')
    mcq: Mapped[List['Mcqs']] = relationship('Mcqs', secondary='project_mcqs', back_populates='project')
    embedding_versions: Mapped[List['EmbeddingVersions']] = relationship('EmbeddingVersions', back_populates='project')


t_student = Table(
    'student', Base.metadata,
    Column('id', Integer),
    Column('name', String)
)


class EmbeddingVersions(Base):
    __tablename__ = 'embedding_versions'
    __table_args__ = (
        ForeignKeyConstraint(['collection_id'], ['langchain_pg_collection.uuid'], ondelete='CASCADE', name='embedding_versions_collection_id_fkey'),
        ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE', name='embedding_versions_project_id_fkey'),
        PrimaryKeyConstraint('version_id', name='embedding_versions_pkey'),
        UniqueConstraint('collection_id', name='unique_collection'),
        UniqueConstraint('project_id', 'version_number', name='unique_project_version'),
        Index('idx_embedding_versions_active', 'project_id', 'is_active'),
        Index('idx_embedding_versions_project', 'project_id')
    )

    version_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    collection_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    version_number: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    description: Mapped[Optional[str]] = mapped_column(Text)
    document_count: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    collection: Mapped['LangchainPgCollection'] = relationship('LangchainPgCollection', back_populates='embedding_versions')
    project: Mapped['Projects'] = relationship('Projects', back_populates='embedding_versions')
    version_documents: Mapped[List['VersionDocuments']] = relationship('VersionDocuments', back_populates='version')


class LangchainPgEmbedding(Base):
    __tablename__ = 'langchain_pg_embedding'
    __table_args__ = (
        ForeignKeyConstraint(['collection_id'], ['langchain_pg_collection.uuid'], ondelete='CASCADE', name='langchain_pg_embedding_collection_id_fkey'),
        PrimaryKeyConstraint('id', name='langchain_pg_embedding_pkey'),
        Index('ix_cmetadata_gin', 'cmetadata')
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    collection_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    embedding: Mapped[Optional[Any]] = mapped_column(VECTOR)
    document: Mapped[Optional[str]] = mapped_column(String)
    cmetadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    collection: Mapped[Optional['LangchainPgCollection']] = relationship('LangchainPgCollection', back_populates='langchain_pg_embedding')


t_project_docs = Table(
    'project_docs', Base.metadata,
    Column('project_id', Uuid, primary_key=True, nullable=False),
    Column('doc_id', Uuid, primary_key=True, nullable=False),
    ForeignKeyConstraint(['doc_id'], ['documents.doc_id'], ondelete='CASCADE', name='project_docs_doc_id_fkey'),
    ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE', name='project_docs_project_id_fkey'),
    PrimaryKeyConstraint('project_id', 'doc_id', name='project_docs_pkey')
)


t_project_mcqs = Table(
    'project_mcqs', Base.metadata,
    Column('project_id', Uuid, primary_key=True, nullable=False),
    Column('mcq_id', Uuid, primary_key=True, nullable=False),
    ForeignKeyConstraint(['mcq_id'], ['mcqs.mcq_id'], ondelete='CASCADE', name='project_mcqs_mcq_id_fkey'),
    ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE', name='project_mcqs_project_id_fkey'),
    PrimaryKeyConstraint('project_id', 'mcq_id', name='project_mcqs_pkey')
)


class VersionDocuments(Base):
    __tablename__ = 'version_documents'
    __table_args__ = (
        ForeignKeyConstraint(['document_id'], ['documents.doc_id'], ondelete='CASCADE', name='version_documents_document_id_fkey'),
        ForeignKeyConstraint(['version_id'], ['embedding_versions.version_id'], ondelete='CASCADE', name='version_documents_version_id_fkey'),
        PrimaryKeyConstraint('id', name='version_documents_pkey'),
        UniqueConstraint('version_id', 'document_id', name='unique_version_document')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    version_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    chunk_count: Mapped[Optional[int]] = mapped_column(Integer)
    processed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    document: Mapped['Documents'] = relationship('Documents', back_populates='version_documents')
    version: Mapped['EmbeddingVersions'] = relationship('EmbeddingVersions', back_populates='version_documents')
