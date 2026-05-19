from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class FormModel(Base):
    __tablename__ = "forms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)

    fields: Mapped[list[FormFieldModel]] = relationship(back_populates="form", cascade="all, delete-orphan")
    submissions: Mapped[list[FormSubmissionModel]] = relationship(back_populates="form", cascade="all, delete-orphan")


class FormFieldModel(Base):
    __tablename__ = "form_fields"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    options: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    field_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validation_rules: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    form: Mapped[FormModel] = relationship(back_populates="fields")


class FormSubmissionModel(Base):
    __tablename__ = "form_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    form_id: Mapped[str] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    form: Mapped[FormModel] = relationship(back_populates="submissions")
    answers: Mapped[list[SubmissionAnswerModel]] = relationship(back_populates="submission", cascade="all, delete-orphan")


class SubmissionAnswerModel(Base):
    __tablename__ = "submission_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    submission_id: Mapped[str] = mapped_column(ForeignKey("form_submissions.id", ondelete="CASCADE"), nullable=False)
    field_id: Mapped[str] = mapped_column(ForeignKey("form_fields.id", ondelete="CASCADE"), nullable=False)
    answer_value: Mapped[object] = mapped_column(JSON, nullable=True)

    submission: Mapped[FormSubmissionModel] = relationship(back_populates="answers")
