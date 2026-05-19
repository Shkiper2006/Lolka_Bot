from __future__ import annotations

from typing import Any

from storage.db import session_scope
from storage.repositories import FormSubmissionsRepository, SubmissionAnswersRepository


class SubmitFormService:
    """Транзакционный submit-flow: создание отправки + ответы атомарно."""

    def submit(self, form_id: str, user_id: str, answers: dict[str, Any]) -> str:
        with session_scope() as session:
            submission_repo = FormSubmissionsRepository(session)
            answers_repo = SubmissionAnswersRepository(session)

            submission = submission_repo.create(form_id=form_id, user_id=user_id, status="submitted")
            answers_repo.bulk_create(submission_id=submission.id, answers=answers)
            return submission.id
