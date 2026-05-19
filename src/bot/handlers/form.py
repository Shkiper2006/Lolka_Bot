from integrations.lolka_client import LolkaClient
from bot.forms_service import FormService


FORM_SERVICE = FormService()


async def handle_form_create(client: LolkaClient, channel_id: str, created_by: str = "system") -> dict:
    form = FORM_SERVICE.create_form(
        title="Новая форма",
        description="Форма, созданная через /form create",
        created_by=created_by,
    )
    return await client.send_channel_message(channel_id, f"Форма создана: {form.id}")


async def handle_form_fill(client: LolkaClient, channel_id: str, form_id: str) -> dict:
    ui_schema = FORM_SERVICE.as_lolka_ui_schema(form_id)
    return await client.send_channel_message(channel_id, f"Запускаю заполнение формы: {ui_schema}")
