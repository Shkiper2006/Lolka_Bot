from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict
from datetime import timezone
from typing import Any

from bot.forms_service import Form, FormSubmission
from integrations.lolka_client import LolkaClient

logger = logging.getLogger(__name__)


class ReportDeliveryError(RuntimeError):
    pass


def build_report_text(form: Form, submission: FormSubmission) -> str:
    submitted_at = submission.updated_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    answers = []
    for field in form.fields:
        value = submission.answers.get(field.id, "—")
        answers.append(f"- {field.label} → {value}")

    header = [
        "# Отчет по форме",
        f"Форма: {form.title}",
        f"Пользователь: {submission.user_id}",
        f"Дата/время: {submitted_at}",
        "",
        "## Ответы",
        *answers,
        "",
        "## Метаданные",
        f"submission_id: {submission.id}",
        f"form_id: {submission.form_id}",
    ]
    return "\n".join(header)


def build_report_json(form: Form, submission: FormSubmission) -> dict[str, Any]:
    ordered_answers = []
    for field in form.fields:
        ordered_answers.append(
            {
                "field_id": field.id,
                "label": field.label,
                "required": field.required,
                "type": field.type.value,
                "value": submission.answers.get(field.id),
            }
        )

    return {
        "submission_id": submission.id,
        "form_id": form.id,
        "form_title": form.title,
        "user_id": submission.user_id,
        "status": submission.status,
        "submitted_at": submission.updated_at.astimezone(timezone.utc).isoformat(),
        "answers": ordered_answers,
        "form": asdict(form),
    }


async def deliver_report_with_retry(
    client: LolkaClient,
    channel_id: str,
    text_report: str,
    json_payload: dict[str, Any],
    submission_id: str,
    max_attempts: int = 4,
    base_delay_sec: float = 1.0,
) -> None:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            await client.send_channel_message(channel_id, text_report)
            await client.send_channel_message(
                channel_id,
                f"```json\n{json.dumps(json_payload, ensure_ascii=False, indent=2)}\n```",
            )
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.warning(
                "Report delivery failed",
                extra={"submission_id": submission_id, "attempt": attempt, "max_attempts": max_attempts},
            )
            if attempt < max_attempts:
                await asyncio.sleep(base_delay_sec * (2 ** (attempt - 1)))

    logger.error(
        "Report delivery permanently failed",
        extra={
            "submission_id": submission_id,
            "channel_id": channel_id,
            "failure_reason": str(last_error),
            "delivery_status": "failed",
        },
    )
    raise ReportDeliveryError(f"Не удалось отправить отчет submission={submission_id}")
