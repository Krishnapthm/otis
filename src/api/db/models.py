from typing import Optional

from sqlalchemy import Column, DateTime, Integer, PrimaryKeyConstraint, String, Table, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import datetime
import uuid

class Base(DeclarativeBase):
    pass


class Mcqs(Base):
    __tablename__ = 'mcqs'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='mcqs_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text("generate_random_uuid()"))
    generated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    project: Mapped[Optional[str]] = mapped_column(String)
    mcq: Mapped[Optional[dict]] = mapped_column(JSONB)


t_student = Table(
    'student', Base.metadata,
    Column('id', Integer),
    Column('name', String)
)
