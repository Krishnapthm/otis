from typing import Any, Optional
import datetime
import uuid

from pgvector.sqlalchemy.vector import VECTOR
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKeyConstraint, Index, Integer, JSON, LargeBinary, PrimaryKeyConstraint, String, Table, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class CheckpointBlobs(Base):
    __tablename__ = 'checkpoint_blobs'
    __table_args__ = (
        PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'channel', 'version', name='checkpoint_blobs_pkey'),
        Index('checkpoint_blobs_thread_id_idx', 'thread_id')
    )

    thread_id: Mapped[str] = mapped_column(Text, primary_key=True)
    checkpoint_ns: Mapped[str] = mapped_column(Text, primary_key=True, server_default=text("''::text"))
    channel: Mapped[str] = mapped_column(Text, primary_key=True)
    version: Mapped[str] = mapped_column(Text, primary_key=True)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    blob: Mapped[Optional[bytes]] = mapped_column(LargeBinary)


class CheckpointMigrations(Base):
    __tablename__ = 'checkpoint_migrations'
    __table_args__ = (
        PrimaryKeyConstraint('v', name='checkpoint_migrations_pkey'),
    )

    v: Mapped[int] = mapped_column(Integer, primary_key=True)


class CheckpointWrites(Base):
    __tablename__ = 'checkpoint_writes'
    __table_args__ = (
        PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id', 'task_id', 'idx', name='checkpoint_writes_pkey'),
        Index('checkpoint_writes_thread_id_idx', 'thread_id')
    )

    thread_id: Mapped[str] = mapped_column(Text, primary_key=True)
    checkpoint_ns: Mapped[str] = mapped_column(Text, primary_key=True, server_default=text("''::text"))
    checkpoint_id: Mapped[str] = mapped_column(Text, primary_key=True)
    task_id: Mapped[str] = mapped_column(Text, primary_key=True)
    idx: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    task_path: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''::text"))
    type: Mapped[Optional[str]] = mapped_column(Text)


class Checkpoints(Base):
    __tablename__ = 'checkpoints'
    __table_args__ = (
        PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id', name='checkpoints_pkey'),
        Index('checkpoints_thread_id_idx', 'thread_id')
    )

    thread_id: Mapped[str] = mapped_column(Text, primary_key=True)
    checkpoint_ns: Mapped[str] = mapped_column(Text, primary_key=True, server_default=text("''::text"))
    checkpoint_id: Mapped[str] = mapped_column(Text, primary_key=True)
    checkpoint: Mapped[dict] = mapped_column(JSONB, nullable=False)
    metadata_: Mapped[dict] = mapped_column('metadata', JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    parent_checkpoint_id: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[Optional[str]] = mapped_column(Text)


class ConceptCache(Base):
    __tablename__ = 'concept_cache'
    __table_args__ = (
        PrimaryKeyConstraint('cache_id', name='concept_cache_pkey'),
        UniqueConstraint('content_hash', 'extractor_version', name='concept_cache_content_hash_extractor_version_key'),
        Index('idx_concept_cache_expires', 'expires_at'),
        Index('idx_concept_cache_lookup', 'content_hash', 'extractor_version')
    )

    cache_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(50), nullable=False)
    concepts: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text("(now() + '90 days'::interval)"))


class LangchainPgCollection(Base):
    __tablename__ = 'langchain_pg_collection'
    __table_args__ = (
        PrimaryKeyConstraint('uuid', name='langchain_pg_collection_pkey'),
        UniqueConstraint('name', name='langchain_pg_collection_name_key')
    )

    uuid: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    cmetadata: Mapped[Optional[dict]] = mapped_column(JSON)

    langchain_pg_embedding: Mapped[list['LangchainPgEmbedding']] = relationship('LangchainPgEmbedding', back_populates='collection')
    user_vectorstores: Mapped[list['UserVectorstores']] = relationship('UserVectorstores', back_populates='collection')


class McqCache(Base):
    __tablename__ = 'mcq_cache'
    __table_args__ = (
        PrimaryKeyConstraint('cache_id', name='mcq_cache_pkey'),
        UniqueConstraint('concept_set_id', 'generator_version', 'params_hash', name='mcq_cache_concept_set_id_generator_version_params_hash_key'),
        Index('idx_mcq_cache_expires', 'expires_at'),
        Index('idx_mcq_cache_lookup', 'concept_set_id', 'generator_version', 'params_hash')
    )

    cache_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    concept_set_id: Mapped[str] = mapped_column(String(64), nullable=False)
    generator_version: Mapped[str] = mapped_column(String(50), nullable=False)
    params_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    mcqs: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text("(now() + '90 days'::interval)"))


class Projects(Base):
    __tablename__ = 'projects'
    __table_args__ = (
        PrimaryKeyConstraint('project_id', name='projects_pkey'),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    project_desc: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    chats: Mapped[list['Chats']] = relationship('Chats', back_populates='project')
    doc: Mapped[list['Documents']] = relationship('Documents', secondary='project_docs', back_populates='project')
    mcq: Mapped[list['Mcqs']] = relationship('Mcqs', secondary='project_mcqs', back_populates='project')


class SchemaMigrations(Base):
    __tablename__ = 'schema_migrations'
    __table_args__ = (
        PrimaryKeyConstraint('version', name='schema_migrations_pkey'),
    )

    version: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dirty: Mapped[bool] = mapped_column(Boolean, nullable=False)


t_student = Table(
    'student', Base.metadata,
    Column('id', Integer),
    Column('name', String)
)


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', name='users_pkey'),
        UniqueConstraint('email', name='email'),
        UniqueConstraint('email', name='users_email_key')
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    email: Mapped[str] = mapped_column(Text, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    uname: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'user'::text"))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))

    chats: Mapped[list['Chats']] = relationship('Chats', back_populates='user')
    documents: Mapped[list['Documents']] = relationship('Documents', back_populates='user')


class Chats(Base):
    __tablename__ = 'chats'
    __table_args__ = (
        CheckConstraint("status = ANY (ARRAY['active'::text, 'archived'::text, 'deleted'::text])", name='chats_status_check'),
        ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE', name='chats_project_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', name='chats_user_id_fkey'),
        PrimaryKeyConstraint('chat_id', name='chats_pkey'),
        Index('idx_chats_last_message_at', 'last_message_at'),
        Index('idx_chats_project_id', 'project_id'),
        Index('idx_chats_status', 'status'),
        Index('idx_chats_user_id', 'user_id')
    )

    chat_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'::text"))
    total_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    total_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    title: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))
    last_message_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    project: Mapped[Optional['Projects']] = relationship('Projects', back_populates='chats')
    user: Mapped['Users'] = relationship('Users', back_populates='chats')
    chat_messages: Mapped[list['ChatMessages']] = relationship('ChatMessages', back_populates='chat')
    mcqs: Mapped[list['Mcqs']] = relationship('Mcqs', back_populates='chat')


class Documents(Base):
    __tablename__ = 'documents'
    __table_args__ = (
        ForeignKeyConstraint(['canonical_document_id'], ['documents.doc_id'], ondelete='SET NULL', name='documents_canonical_document_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', name='documents_user_id_fkey'),
        PrimaryKeyConstraint('doc_id', name='documents_pkey'),
        Index('idx_documents_user_content_hash', 'user_id', 'content_hash'),
        Index('idx_documents_user_file_hash', 'user_id', 'file_hash', unique=True)
    )

    doc_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    content_md: Mapped[Optional[str]] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(Text)
    is_embedded: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    embedded_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[Optional[str]] = mapped_column(String(20), server_default=text("'ready'::character varying"))
    canonical_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    canonical_document: Mapped[Optional['Documents']] = relationship('Documents', remote_side=[doc_id], back_populates='canonical_document_reverse')
    canonical_document_reverse: Mapped[list['Documents']] = relationship('Documents', remote_side=[canonical_document_id], back_populates='canonical_document')
    user: Mapped['Users'] = relationship('Users', back_populates='documents')
    project: Mapped[list['Projects']] = relationship('Projects', secondary='project_docs', back_populates='doc')


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


class UserVectorstores(Users):
    __tablename__ = 'user_vectorstores'
    __table_args__ = (
        ForeignKeyConstraint(['collection_id'], ['langchain_pg_collection.uuid'], ondelete='SET NULL', name='user_vectorstores_collection_id_fkey'),
        ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE', name='user_vectorstores_user_id_fkey'),
        PrimaryKeyConstraint('user_id', name='user_vectorstores_pkey')
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    collection_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    document_count: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    status: Mapped[Optional[str]] = mapped_column(String(50), server_default=text("'pending'::character varying"))
    job_id: Mapped[Optional[str]] = mapped_column(String(100))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    last_synced_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    collection: Mapped[Optional['LangchainPgCollection']] = relationship('LangchainPgCollection', back_populates='user_vectorstores')


class ChatMessages(Base):
    __tablename__ = 'chat_messages'
    __table_args__ = (
        CheckConstraint("role = ANY (ARRAY['user'::text, 'assistant'::text, 'tool'::text])", name='chat_messages_role_check'),
        CheckConstraint("status = ANY (ARRAY['pending'::text, 'streaming'::text, 'completed'::text, 'failed'::text])", name='chat_messages_status_check'),
        ForeignKeyConstraint(['chat_id'], ['chats.chat_id'], ondelete='CASCADE', name='chat_messages_chat_id_fkey'),
        PrimaryKeyConstraint('message_id', name='chat_messages_pkey'),
        Index('idx_messages_chat_id', 'chat_id'),
        Index('idx_messages_chat_sequence', 'chat_id', 'sequence')
    )

    message_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    chat_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'completed'::text"))
    content: Mapped[Optional[str]] = mapped_column(Text)
    structured_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    error: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))

    chat: Mapped['Chats'] = relationship('Chats', back_populates='chat_messages')
    mcqs: Mapped[list['Mcqs']] = relationship('Mcqs', back_populates='message')


t_project_docs = Table(
    'project_docs', Base.metadata,
    Column('project_id', Uuid, primary_key=True),
    Column('doc_id', Uuid, primary_key=True),
    ForeignKeyConstraint(['doc_id'], ['documents.doc_id'], ondelete='CASCADE', name='project_docs_doc_id_fkey'),
    ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE', name='project_docs_project_id_fkey'),
    PrimaryKeyConstraint('project_id', 'doc_id', name='project_docs_pkey')
)


class Mcqs(Base):
    __tablename__ = 'mcqs'
    __table_args__ = (
        ForeignKeyConstraint(['chat_id'], ['chats.chat_id'], ondelete='SET NULL', name='mcqs_chat_id_fkey'),
        ForeignKeyConstraint(['message_id'], ['chat_messages.message_id'], ondelete='SET NULL', name='mcqs_message_id_fkey'),
        PrimaryKeyConstraint('mcq_id', name='mcqs_pkey'),
        Index('idx_mcqs_chat_id', 'chat_id')
    )

    mcq_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    generated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    mcq: Mapped[Optional[dict]] = mapped_column(JSONB)
    chat_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    chat: Mapped[Optional['Chats']] = relationship('Chats', back_populates='mcqs')
    message: Mapped[Optional['ChatMessages']] = relationship('ChatMessages', back_populates='mcqs')
    project: Mapped[list['Projects']] = relationship('Projects', secondary='project_mcqs', back_populates='mcq')


t_project_mcqs = Table(
    'project_mcqs', Base.metadata,
    Column('project_id', Uuid, primary_key=True),
    Column('mcq_id', Uuid, primary_key=True),
    ForeignKeyConstraint(['mcq_id'], ['mcqs.mcq_id'], ondelete='CASCADE', name='project_mcqs_mcq_id_fkey'),
    ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE', name='project_mcqs_project_id_fkey'),
    PrimaryKeyConstraint('project_id', 'mcq_id', name='project_mcqs_pkey')
)
