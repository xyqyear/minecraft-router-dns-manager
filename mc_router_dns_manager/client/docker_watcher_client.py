import asyncio
from typing import Callable

import aiohttp

from ..logger import logger
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

    async def listen_to_ws(self, on_message: Callable[..., None]):
        """
        should be called in conjunction with asyncio.create_task,
        since it's a infinite loop
        """
        while True:
            try:
                logger.info("connecting to docker watcher ws...")
                async with self._session.ws_connect(self._url + "ws", timeout=self._timeout) as ws:  # type: ignore
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:  # type: ignore
                            logger.info(f"received docker message: {msg.json()}")
                            on_message()
            except Exception as e:
                logger.warning(f"error while connecting docker watcher with ws: {e}")
            logger.info("connection to docker watcher ws closed")
            await asyncio.sleep(self._timeout)

    async def get_servers(self) -> ServersT:
        async with self._session.get(self._url + "all_servers") as response:
            return await response.json()
