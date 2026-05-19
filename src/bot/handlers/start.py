from integrations.lolka_client import LolkaClient


async def handle_start(client: LolkaClient, channel_id: str) -> dict:
    message = (
        "Привет! Я бот для работы с формами.\n"
        "Доступные команды:\n"
        "/start\n"
        "/form create\n"
        "/form fill <form_id>"
    )
    return await client.send_channel_message(channel_id, message)
