import asyncio
import logging
from typing import Awaitable, Callable

import aiohttp

from ..router.mcrouter import ServersT


class DockerWatcherClient:
    def __init__(self, base_url: str, timeout: int = 5) -> None:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        )

        self._timeout = timeout

        self._url = base_url
        if not self._url.endswith("/"):
            self._url += "/"

    async def listen_to_ws(self, on_message: Callable[..., Awaitable[None]]):
        """
        should be called in conjunction with asyncio.create_task,
        since it's a infinite loop
        """
        while True:
            try:
                async with self._session.ws_connect(self._url + "ws", timeout=self._timeout) as ws:  # type: ignore
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:  # type: ignore
                            await on_message()
            except Exception as e:
                logging.warning(f"error while connecting docker watcher with ws: {e}")
            await asyncio.sleep(self._timeout)

    async def get_servers(self) -> ServersT:
        async with self._session.get(self._url + "all_servers") as response:
            return await response.json()
