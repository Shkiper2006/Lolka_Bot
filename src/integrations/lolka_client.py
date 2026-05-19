import logging
from typing import Any, AsyncIterator

import aiohttp


logger = logging.getLogger(__name__)


class LolkaClient:
    def __init__(self, token: str, base_url: str) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "LolkaClient":
        self._session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session:
            await self._session.close()

    async def send_channel_message(self, channel_id: str, content: str) -> dict[str, Any]:
        payload = {"channel_id": channel_id, "content": content}
        return await self._request("POST", "/v1/messages", json=payload)

    async def send_interactive_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/v1/interactions/events", json=event)

    async def receive_interactive_events(self) -> AsyncIterator[dict[str, Any]]:
        if not self._session:
            raise RuntimeError("LolkaClient is not initialized")

        ws_url = self._base_url.replace("http", "ws") + "/v1/interactions/stream"
        logger.info("Connecting to Lolka WebSocket for interactive events")
        async with self._session.ws_connect(ws_url) as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    yield msg.json()
                elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                    logger.warning("WebSocket closed or errored: %s", msg.type)
                    break

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        if not self._session:
            raise RuntimeError("LolkaClient is not initialized")

        url = f"{self._base_url}{path}"
        logger.info("Lolka API request", extra={"request_id": kwargs.get("request_id", "-")})
        async with self._session.request(method, url, **kwargs) as response:
            text = await response.text()
            if response.status >= 400:
                logger.error("Lolka API error: status=%s body=%s", response.status, text)
                raise RuntimeError(f"Lolka API request failed with status {response.status}: {text}")
            if not text:
                return {}
            return await response.json()
