from integrations.lolka_client import LolkaClient


async def handle_form_create(client: LolkaClient, channel_id: str) -> dict:
    return await client.send_channel_message(channel_id, "Создание формы: отправьте название формы.")


async def handle_form_fill(client: LolkaClient, channel_id: str, form_id: str) -> dict:
    return await client.send_channel_message(channel_id, f"Запускаю заполнение формы {form_id}.")
