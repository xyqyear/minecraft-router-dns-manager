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
from typing import Optional

from .client.docker_watcher_client import DockerWatcherClient
from .client.natmap_monitor_client import NatmapMonitorClient
from .dns.mcdns import MCDNS
from .logger import logger
from .manager.local import Local
from .manager.remote import Remote
from .router.mcrouter import MCRouter


class Monitorer:
    def __init__(
        self,
        mcdns: MCDNS,
        mcrouter: MCRouter,
        docker_watcher: DockerWatcherClient,
        natmap_monitor: Optional[NatmapMonitorClient],
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

        self._backoff_timer = 2

    def _queue_update(self):
        logger.info("queueing update from ws event")
        self._update_queue += 1

    async def _update(self):
        """
        :return: True if have updated, False otherwise
        """
        logger.debug("checking for updates...")
        remote_pull_result, local_pull_result = await asyncio.gather(
            self._remote.pull(), self._local.pull()
        )
        if remote_pull_result == local_pull_result:
            return False

        logger.info(f"pushing changes: {local_pull_result}")
        await self._remote.push(local_pull_result.addresses, local_pull_result.servers)
        return True

    async def _try_update(self):
        await asyncio.sleep(self._backoff_timer - 2)
        try:
            async with self._update_lock:
                if await self._update():
                    # wait for 60 seconds for the dns provider to update
                    await asyncio.sleep(60)
            # reset backoff timer if successful
            # (not necessarily having updated, just that the request is successful)
            self._backoff_timer = 2
        except Exception as e:
            logger.warning(f"error while updating: {e}")
            # set a maximum backoff timer of 60 seconds (roughly)
            if self._backoff_timer < 60:
                self._backoff_timer *= 1.5

    async def _check_queue_loop(self):
        while True:
            if self._update_queue > 0:
                self._update_queue -= 1
                await self._try_update()
            await asyncio.sleep(1)

    async def run(self):
        logger.info("running initial check...")
        while True:
            try:
                await self._update()
                break
            except Exception as e:
                logger.warning(f"error while initializing: {e}")
                await asyncio.sleep(self._backoff_timer - 2)
                self._backoff_timer *= 1.5
        self._backoff_timer = 2
        logger.info("initial check done.")

        asyncio.create_task(self._docker_watcher.listen_to_ws(self._queue_update))
        if self._natmap_monitor:
            asyncio.create_task(self._natmap_monitor.listen_to_ws(self._queue_update))

        # the loop for checking ws events
        asyncio.create_task(self._check_queue_loop())

        # the loop for polling
        while True:
            await asyncio.sleep(self._poll_interval)
            await self._try_update()
