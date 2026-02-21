from typing import Any, List, Optional

from pgvector.sqlalchemy.vector import VECTOR
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Computed, DateTime, ForeignKeyConstraint, Index, Integer, JSON, LargeBinary, Numeric, PrimaryKeyConstraint, String, Table, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import datetime
import decimal
import uuid

class Base(DeclarativeBase):
    pass


class Assistant(Base):
    __tablename__ = 'assistant'
    __table_args__ = (
        PrimaryKeyConstraint('assistant_id', name='assistant_pkey'),
        Index('assistant_created_at_idx', 'created_at'),
        Index('assistant_graph_id_idx', 'graph_id', 'created_at'),
        Index('assistant_metadata_idx', 'metadata')
    )

    assistant_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    graph_id: Mapped[str] = mapped_column(Text)
    config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"))
    version: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    name: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    context: Mapped[Optional[dict]] = mapped_column(JSONB)

    assistant_versions: Mapped[List['AssistantVersions']] = relationship('AssistantVersions', back_populates='assistant')
    cron: Mapped[List['Cron']] = relationship('Cron', back_populates='assistant')


class CheckpointBlobs(Base):
    __tablename__ = 'checkpoint_blobs'
    __table_args__ = (
        PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'channel', 'version', name='checkpoint_blobs_pkey'),
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    channel: Mapped[str] = mapped_column(Text, primary_key=True)
    version: Mapped[str] = mapped_column(Text, primary_key=True)
    type: Mapped[str] = mapped_column(Text)
    checkpoint_ns: Mapped[str] = mapped_column(Text, primary_key=True, server_default=text("''::text"))
    blob: Mapped[Optional[bytes]] = mapped_column(LargeBinary)


class CheckpointWrites(Base):
    __tablename__ = 'checkpoint_writes'
    __table_args__ = (
        PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id', 'task_id', 'idx', name='checkpoint_writes_pkey'),
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    checkpoint_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    task_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    idx: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(Text)
    blob: Mapped[bytes] = mapped_column(LargeBinary)
    checkpoint_ns: Mapped[str] = mapped_column(Text, primary_key=True, server_default=text("''::text"))


class Checkpoints(Base):
    __tablename__ = 'checkpoints'
    __table_args__ = (
        PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id', name='checkpoints_pkey'),
        Index('checkpoints_checkpoint_id_idx', 'thread_id', 'checkpoint_id'),
        Index('checkpoints_run_id_idx', 'run_id')
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    checkpoint_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    checkpoint: Mapped[dict] = mapped_column(JSONB)
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"))
    checkpoint_ns: Mapped[str] = mapped_column(Text, primary_key=True, server_default=text("''::text"))
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    parent_checkpoint_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)


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
    content_md: Mapped[Optional[str]] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(Text)

    project: Mapped[List['Projects']] = relationship('Projects', secondary='project_docs', back_populates='doc')
    version_documents: Mapped[List['VersionDocuments']] = relationship('VersionDocuments', back_populates='document')


class LangchainPgCollection(Base):
    __tablename__ = 'langchain_pg_collection'
    __table_args__ = (
        PrimaryKeyConstraint('uuid', name='langchain_pg_collection_pkey'),
        UniqueConstraint('name', name='langchain_pg_collection_name_key')
    )

    uuid: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    cmetadata: Mapped[Optional[dict]] = mapped_column(JSON)

    embedding_versions: Mapped[Optional['EmbeddingVersions']] = relationship('EmbeddingVersions', uselist=False, back_populates='collection')
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
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid)
    project_desc: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    doc: Mapped[List['Documents']] = relationship('Documents', secondary='project_docs', back_populates='project')
    mcq: Mapped[List['Mcqs']] = relationship('Mcqs', secondary='project_mcqs', back_populates='project')
    embedding_versions: Mapped[List['EmbeddingVersions']] = relationship('EmbeddingVersions', back_populates='project')


class Run(Base):
    __tablename__ = 'run'
    __table_args__ = (
        PrimaryKeyConstraint('run_id', name='run_pkey'),
        Index('idx_run_thread_running', 'thread_id'),
        Index('run_pending_by_thread_time', 'thread_id', 'created_at'),
        Index('run_pending_idx', 'created_at'),
        Index('run_thread_id_status_idx', 'thread_id', 'status')
    )

    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    assistant_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(Text, server_default=text("'pending'::text"))
    kwargs: Mapped[dict] = mapped_column(JSONB)
    multitask_strategy: Mapped[str] = mapped_column(Text, server_default=text("'reject'::text"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))


class SchemaMigrations(Base):
    __tablename__ = 'schema_migrations'
    __table_args__ = (
        PrimaryKeyConstraint('version', name='schema_migrations_pkey'),
    )

    version: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dirty: Mapped[bool] = mapped_column(Boolean)


class Store(Base):
    __tablename__ = 'store'
    __table_args__ = (
        PrimaryKeyConstraint('prefix', 'key', name='store_pkey'),
        Index('idx_store_expires_at', 'expires_at'),
        Index('store_prefix_idx', 'prefix')
    )

    prefix: Mapped[str] = mapped_column(Text, primary_key=True)
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('CURRENT_TIMESTAMP'))
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    ttl_minutes: Mapped[Optional[int]] = mapped_column(Integer)


t_student = Table(
    'student', Base.metadata,
    Column('id', Integer),
    Column('name', String)
)


class Thread(Base):
    __tablename__ = 'thread'
    __table_args__ = (
        PrimaryKeyConstraint('thread_id', name='thread_pkey'),
        Index('thread_created_at_idx', 'created_at'),
        Index('thread_metadata_idx', 'metadata'),
        Index('thread_owner_updated_idx', 'updated_at', 'thread_id'),
        Index('thread_status_idx', 'status', 'created_at'),
        Index('thread_values_idx', 'values')
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"))
    status: Mapped[str] = mapped_column(Text, server_default=text("'idle'::text"))
    config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    interrupts: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    values: Mapped[Optional[dict]] = mapped_column(JSONB)
    error: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

    cron: Mapped[List['Cron']] = relationship('Cron', back_populates='thread')
    thread_ttl: Mapped[List['ThreadTtl']] = relationship('ThreadTtl', back_populates='thread')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', name='users_pkey'),
        UniqueConstraint('email', name='users_email_key'),
        UniqueConstraint('email', name='email')
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    email: Mapped[str] = mapped_column(Text)
    hashed_password: Mapped[str] = mapped_column(Text)
    uname: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(Text, server_default=text("'user'::text"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))


class AssistantVersions(Base):
    __tablename__ = 'assistant_versions'
    __table_args__ = (
        ForeignKeyConstraint(['assistant_id'], ['assistant.assistant_id'], ondelete='CASCADE', name='assistant_versions_assistant_id_fkey'),
        PrimaryKeyConstraint('assistant_id', 'version', name='assistant_versions_pkey')
    )

    assistant_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    version: Mapped[int] = mapped_column(Integer, primary_key=True, server_default=text('1'))
    graph_id: Mapped[str] = mapped_column(Text)
    config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    name: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    context: Mapped[Optional[dict]] = mapped_column(JSONB)

    assistant: Mapped['Assistant'] = relationship('Assistant', back_populates='assistant_versions')


class Cron(Base):
    __tablename__ = 'cron'
    __table_args__ = (
        CheckConstraint("on_run_completed::text = ANY (ARRAY['delete'::character varying, 'keep'::character varying]::text[])", name='cron_on_run_completed_check'),
        ForeignKeyConstraint(['assistant_id'], ['assistant.assistant_id'], ondelete='CASCADE', name='cron_assistant_id_fkey'),
        ForeignKeyConstraint(['thread_id'], ['thread.thread_id'], ondelete='CASCADE', name='cron_thread_id_fkey'),
        PrimaryKeyConstraint('cron_id', name='cron_pkey')
    )

    cron_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    payload: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    schedule: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB, server_default=text("'{}'::jsonb"))
    assistant_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    user_id: Mapped[Optional[str]] = mapped_column(Text)
    next_run_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    on_run_completed: Mapped[Optional[str]] = mapped_column(String(20), server_default=text("'delete'::character varying"), comment='What to do with the thread after the run completes: delete removes the thread after execution, keep creates a new thread for each execution but does not clean them up. This parameter is only applicable when thread_id is NULL; when thread_id is present, on_run_completed is ignored.')

    assistant: Mapped[Optional['Assistant']] = relationship('Assistant', back_populates='cron')
    thread: Mapped[Optional['Thread']] = relationship('Thread', back_populates='cron')


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
    version_number: Mapped[int] = mapped_column(Integer)
    collection_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    description: Mapped[Optional[str]] = mapped_column(Text)
    document_count: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    version_name: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[Optional[str]] = mapped_column(String(20), server_default=text("'pending'::character varying"))
    job_id: Mapped[Optional[str]] = mapped_column(String(100))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    collection: Mapped[Optional['LangchainPgCollection']] = relationship('LangchainPgCollection', back_populates='embedding_versions')
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


class ThreadTtl(Base):
    __tablename__ = 'thread_ttl'
    __table_args__ = (
        CheckConstraint('ttl_minutes >= 0::numeric', name='thread_ttl_ttl_minutes_check'),
        ForeignKeyConstraint(['thread_id'], ['thread.thread_id'], ondelete='CASCADE', name='thread_ttl_thread_id_fkey'),
        PrimaryKeyConstraint('id', name='thread_ttl_pkey'),
        Index('idx_thread_ttl_expires_at', 'expires_at'),
        Index('idx_thread_ttl_thread_strategy', 'thread_id', 'strategy', unique=True)
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    strategy: Mapped[str] = mapped_column(Text, server_default=text("'delete'::text"))
    ttl_minutes: Mapped[decimal.Decimal] = mapped_column(Numeric)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=text("(CURRENT_TIMESTAMP AT TIME ZONE 'UTC'::text)"))
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, Computed("(created_at + ((ttl_minutes)::double precision * '00:01:00'::interval))", persisted=True))

    thread: Mapped['Thread'] = relationship('Thread', back_populates='thread_ttl')


class VersionDocuments(Base):
    __tablename__ = 'version_documents'
    __table_args__ = (
        ForeignKeyConstraint(['document_id'], ['documents.doc_id'], ondelete='CASCADE', name='version_documents_document_id_fkey'),
        ForeignKeyConstraint(['version_id'], ['embedding_versions.version_id'], ondelete='CASCADE', name='version_documents_version_id_fkey'),
        PrimaryKeyConstraint('version_id', 'document_id', name='version_documents_pkey')
    )

    version_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    processed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    document: Mapped['Documents'] = relationship('Documents', back_populates='version_documents')
    version: Mapped['EmbeddingVersions'] = relationship('EmbeddingVersions', back_populates='version_documents')
