from typing import List, Optional

from sqlalchemy import Column, DateTime, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, String, Table, Uuid, text
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
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    file_path: Mapped[str] = mapped_column(String)

    project: Mapped[List['Projects']] = relationship('Projects', secondary='project_docs', back_populates='doc')


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

    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('get_random_uuid()'))
    project_name: Mapped[str] = mapped_column(String)
    project_desc: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('now()'))

    doc: Mapped[List['Documents']] = relationship('Documents', secondary='project_docs', back_populates='project')
    mcq: Mapped[List['Mcqs']] = relationship('Mcqs', secondary='project_mcqs', back_populates='project')


t_student = Table(
    'student', Base.metadata,
    Column('id', Integer),
    Column('name', String)
)


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
