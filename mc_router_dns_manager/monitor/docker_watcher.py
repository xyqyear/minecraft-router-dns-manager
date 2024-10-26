import asyncio
from pathlib import Path
from typing import Callable

from minecraft_docker_manager_lib.manager import DockerMCManager

from ..config import config
from ..logger import logger
from ..router.mcrouter import ServersT


class DockerWatcher:
    def __init__(self, servers_root_path: str | Path) -> None:
        self._servers_root_path = servers_root_path
        self._docker_mc_manager = DockerMCManager(self._servers_root_path)
        self._previous_servers: ServersT | None = None

    async def get_servers(self) -> ServersT:
        server_info_list = await self._docker_mc_manager.get_all_server_info()
        return {
            server_info.name: server_info.game_port for server_info in server_info_list
        }

    async def watch_servers(self, on_change: Callable[..., None]):
        while True:
            try:
                servers = await self.get_servers()
                if servers != self._previous_servers:
                    on_change()
                    self._previous_servers = servers
            except Exception as e:
                logger.warning(f"error while watching servers: {e}")
            await asyncio.sleep(config.docker_watcher.poll_interval)
