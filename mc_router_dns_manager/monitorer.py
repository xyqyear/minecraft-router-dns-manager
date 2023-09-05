"""
This class should be responsible for the following:
- checks docker file monitor and natmap service (if neccessary) for changes
- listens to ws events from those services as well
- whenever there is an event (be it from ws or from polling)
    - pull info from dns and mc-router
    - checks if server_list from dns matches the ones from mc-router
    - also checks if there is any change
    - if there is a change, call the callback function

Specifically, when initializing, it should check for changes once 
    and call the callback function if there is any change (indefinitely retrying if there is an error)

I think there should also be a queue for events that are not yet processed
"""
import asyncio
import logging

from .client.docker_watcher_client import DockerWatcherClient
from .client.natmap_monitor_client import NatmapMonitorClient
from .dns.mcdns import MCDNS
from .manager.local import Local
from .manager.remote import Remote
from .router.mcrouter import MCRouter
from .config import config


class Monitorer:
    def __init__(
        self,
        mcdns: MCDNS,
        mcrouter: MCRouter,
        docker_watcher: DockerWatcherClient,
        natmap_monitor: NatmapMonitorClient,
        poll_interval: int,
    ) -> None:
        self._docker_watcher = docker_watcher
        self._natmap_monitor = natmap_monitor

        self._remote = Remote(mcrouter, mcdns)
        self._local = Local(docker_watcher, natmap_monitor)

        self._poll_interval = poll_interval

        # the queue is only for ws events
        self._update_queue = 0
        self._update_lock = asyncio.Lock()

    def _queue_update(self):
        self._update_queue += 1

    async def _update(self):
        remote_pull_result, local_pull_result = await asyncio.gather(
            self._remote.pull(), self._local.pull()
        )
        if remote_pull_result == local_pull_result:
            return
        else:
            await self._remote.push(
                local_pull_result.addresses, local_pull_result.servers
            )

    async def _try_update(self):
        try:
            async with self._update_lock:
                await self._update()
        except Exception as e:
            logging.warning(f"error while updating: {e}")

    async def _check_queue_loop(self):
        while True:
            if self._update_queue > 0:
                self._update_queue -= 1
                await self._try_update()
            await asyncio.sleep(1)

    async def run(self):
        while True:
            try:
                await self._update()
                break
            except Exception as e:
                logging.warning(f"error while initializing: {e}")

        asyncio.create_task(self._docker_watcher.listen_to_ws(self._queue_update))
        if config["natmap_monitor"]["enabled"]:
            asyncio.create_task(self._natmap_monitor.listen_to_ws(self._queue_update))

        # the loop for checking ws events
        asyncio.create_task(self._check_queue_loop())

        # the loop for polling
        while True:
            await self._try_update()
            await asyncio.sleep(self._poll_interval)
