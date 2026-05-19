from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from storage.models import FormFieldModel, FormModel, FormSubmissionModel, SubmissionAnswerModel


class FormsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, title: str, description: str, created_by: str, status: str = "draft") -> FormModel:
        model = FormModel(title=title, description=description, created_by=created_by, status=status)
        self.session.add(model)
        self.session.flush()
        return model

    def get(self, form_id: str) -> FormModel | None:
        stmt = select(FormModel).where(FormModel.id == form_id).options(selectinload(FormModel.fields))
        return self.session.scalar(stmt)


class FormFieldsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def bulk_create(self, form_id: str, fields: list[dict[str, Any]]) -> list[FormFieldModel]:
        models = [FormFieldModel(form_id=form_id, **payload) for payload in fields]
        self.session.add_all(models)
        self.session.flush()
        return models


class FormSubmissionsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, form_id: str, user_id: str, status: str = "submitted") -> FormSubmissionModel:
        now = datetime.now(timezone.utc)
        model = FormSubmissionModel(form_id=form_id, user_id=user_id, status=status, created_at=now, updated_at=now)
        self.session.add(model)
        self.session.flush()
        return model


class SubmissionAnswersRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def bulk_create(self, submission_id: str, answers: dict[str, Any]) -> list[SubmissionAnswerModel]:
        rows = [
            SubmissionAnswerModel(submission_id=submission_id, field_id=field_id, answer_value=value)
            for field_id, value in answers.items()
        ]
        self.session.add_all(rows)
        self.session.flush()
        return rows
