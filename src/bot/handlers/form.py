from integrations.lolka_client import LolkaClient
from bot.forms_service import FormService
from bot.forms_service import FormField, FormFieldType, FormValidationError
from bot.reporting import ReportDeliveryError, build_report_json, build_report_text, deliver_report_with_retry
from config.settings import Settings


FORM_SERVICE = FormService()
ACTIVE_SESSIONS: dict[tuple[str, str], dict] = {}


async def handle_form_create(client: LolkaClient, channel_id: str, created_by: str = "system") -> dict:
    form = FORM_SERVICE.create_form(
        title="Новая форма",
        description="Форма, созданная через /form create",
        created_by=created_by,
    )
    return await client.send_channel_message(channel_id, f"Форма создана: {form.id}")


async def handle_form_fill(client: LolkaClient, channel_id: str, form_id: str) -> dict:
    form = FORM_SERVICE.get_form(form_id)
    if not form.fields:
        return await client.send_channel_message(channel_id, "У формы нет полей для заполнения.")
    ui_schema = FORM_SERVICE.as_lolka_ui_schema(form_id)
    return await client.send_channel_message(
        channel_id,
        f"Форма готова к заполнению.\nWeb-view schema: {ui_schema}\n"
        "Если web-view недоступен, используйте диалог: /form dialog <form_id>",
    )


async def handle_form_dialog_start(client: LolkaClient, channel_id: str, user_id: str, form_id: str) -> dict:
    form = FORM_SERVICE.get_form(form_id)
    if not form.fields:
        return await client.send_channel_message(channel_id, "У формы нет полей для заполнения.")

    draft = FORM_SERVICE.get_draft_submission(form_id, user_id)
    answers = dict(draft.answers) if draft else {}
    step = min(len(answers), len(form.fields) - 1)
    ACTIVE_SESSIONS[(channel_id, user_id)] = {"form_id": form_id, "step": step, "answers": answers, "mode": "questions"}
    return await _send_question(client, channel_id, user_id)


async def handle_form_dialog_message(client: LolkaClient, channel_id: str, user_id: str, text: str) -> dict:
    session = ACTIVE_SESSIONS.get((channel_id, user_id))
    if not session:
        return {"ok": True}
    if session.get("mode") == "confirm":
        return await handle_form_dialog_confirm(client, channel_id, user_id, text)

    command = text.strip().lower()
    if command == "отмена":
        del ACTIVE_SESSIONS[(channel_id, user_id)]
        return await client.send_channel_message(channel_id, "Заполнение формы отменено. Черновик сохранён.")

    if command == "назад":
        session["step"] = max(0, session["step"] - 1)
        return await _send_question(client, channel_id, user_id)

    form = FORM_SERVICE.get_form(session["form_id"])
    field = form.fields[session["step"]]
    if command == "пропустить" and not field.required:
        session["answers"].pop(field.id, None)
    elif command == "пропустить":
        return await client.send_channel_message(channel_id, "Это обязательное поле, его нельзя пропустить.")
    else:
        try:
            session["answers"][field.id] = _parse_answer(field, text)
            FORM_SERVICE._validate_answers(form, {field.id: session["answers"][field.id]})
        except (ValueError, FormValidationError) as exc:
            return await client.send_channel_message(channel_id, f"Ошибка в ответе: {exc}")

    FORM_SERVICE.save_draft_submission(session["form_id"], user_id, session["answers"])

    if session["step"] + 1 >= len(form.fields):
        return await _send_preview(client, channel_id, user_id)
    session["step"] += 1
    return await _send_question(client, channel_id, user_id)


async def handle_form_dialog_confirm(client: LolkaClient, channel_id: str, user_id: str, text: str) -> dict:
    session = ACTIVE_SESSIONS.get((channel_id, user_id))
    if not session:
        return {"ok": True}
    if text.strip().lower() == "подтвердить":
        submission = FORM_SERVICE.complete_draft_submission(session["form_id"], user_id, session["answers"])
        form = FORM_SERVICE.get_form(session["form_id"])
        report_text = build_report_text(form, submission)
        report_payload = build_report_json(form, submission)
        settings = Settings.from_env()
        delivery_error = None
        try:
            await deliver_report_with_retry(
                client=client,
                channel_id=settings.lolka_report_channel_id,
                text_report=report_text,
                json_payload=report_payload,
                submission_id=submission.id,
            )
        except ReportDeliveryError:
            delivery_error = " Отчет будет доставлен позже: отправка в канал временно недоступна."

        del ACTIVE_SESSIONS[(channel_id, user_id)]
        return await client.send_channel_message(
            channel_id,
            f"Форма отправлена успешно. ID отправки: {submission.id}.{delivery_error or ''}",
        )
    if text.strip().lower() == "назад":
        form = FORM_SERVICE.get_form(session["form_id"])
        session["step"] = len(form.fields) - 1
        session["mode"] = "questions"
        return await _send_question(client, channel_id, user_id)
    return await client.send_channel_message(channel_id, "Напишите 'подтвердить' для отправки или 'назад' для правки.")


async def _send_question(client: LolkaClient, channel_id: str, user_id: str) -> dict:
    session = ACTIVE_SESSIONS[(channel_id, user_id)]
    form = FORM_SERVICE.get_form(session["form_id"])
    field = form.fields[session["step"]]
    optional_hint = "" if field.required else " (можно: 'пропустить')"
    return await client.send_channel_message(
        channel_id,
        f"[{session['step'] + 1}/{len(form.fields)}] {field.label}{optional_hint}\n"
        "Команды: назад / пропустить / отмена",
    )


async def _send_preview(client: LolkaClient, channel_id: str, user_id: str) -> dict:
    session = ACTIVE_SESSIONS[(channel_id, user_id)]
    session["mode"] = "confirm"
    form = FORM_SERVICE.get_form(session["form_id"])
    lines = ["Предпросмотр перед отправкой:"]
    for field in form.fields:
        lines.append(f"- {field.label}: {session['answers'].get(field.id, '—')}")
    lines.append("Напишите 'подтвердить' для отправки или 'назад' для редактирования.")
    return await client.send_channel_message(channel_id, "\n".join(lines))


def _parse_answer(field: FormField, raw: str):
    value = raw.strip()
    if field.type in (FormFieldType.SHORT_TEXT, FormFieldType.LONG_TEXT, FormFieldType.DATE):
        return value
    if field.type == FormFieldType.NUMBER:
        return float(value) if "." in value else int(value)
    if field.type == FormFieldType.BOOLEAN:
        if value.lower() in ("да", "yes", "true", "1"):
            return True
        if value.lower() in ("нет", "no", "false", "0"):
            return False
        raise ValueError("Булево поле: используйте да/нет")
    if field.type == FormFieldType.SELECT:
        return value
    if field.type == FormFieldType.MULTISELECT:
        return [item.strip() for item in value.split(",") if item.strip()]
    return value
