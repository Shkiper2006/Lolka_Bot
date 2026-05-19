import asyncio
import logging

from bot.error_handler import safe_handler
from bot.handlers.form import handle_form_create, handle_form_dialog_message, handle_form_dialog_start, handle_form_fill
from bot.handlers.start import handle_start
from config.logging import configure_logging
from config.settings import Settings
from integrations.lolka_client import LolkaClient

logger = logging.getLogger(__name__)


@safe_handler
async def route_command(client: LolkaClient, channel_id: str, user_id: str, text: str) -> dict:
    parts = text.strip().split()
    if not parts:
        return {"ok": True}

    if parts[0] == "/start":
        return await handle_start(client, channel_id)

    if parts[0] == "/form" and len(parts) >= 2:
        if parts[1] == "create":
            return await handle_form_create(client, channel_id)
        if parts[1] == "fill" and len(parts) >= 3:
            return await handle_form_fill(client, channel_id, parts[2])
        if parts[1] == "dialog" and len(parts) >= 3:
            return await handle_form_dialog_start(client, channel_id, user_id, parts[2])

    return await handle_form_dialog_message(client, channel_id, user_id, text)


async def run() -> None:
    configure_logging()
    settings = Settings.from_env()

    async with LolkaClient(settings.lolka_token, settings.lolka_api_base_url) as client:
        logger.info("Bot started for server %s", settings.lolka_server_id)
        await client.send_channel_message(settings.lolka_report_channel_id, "Бот запущен и готов к работе.")

        # Placeholder event loop for interactive events.
        async for event in client.receive_interactive_events():
            channel_id = event.get("channel_id", settings.lolka_report_channel_id)
            text = event.get("text", "")
            user_id = event.get("user_id", "anonymous")
            await route_command(client, channel_id, user_id, text)


if __name__ == "__main__":
    asyncio.run(run())
