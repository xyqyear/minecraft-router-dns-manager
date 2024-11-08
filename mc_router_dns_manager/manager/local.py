"""
Responsibility: update mc-router and dns records with relevant information
"""

from typing import NamedTuple, Optional

from ..config import config
from ..dns.mcdns import AddressesT, AddressInfoT
from ..monitor.docker_watcher import DockerWatcher
from ..monitor.natmap_monitor_client import NatmapMonitorClient
from ..router.mcrouter import ServersT


class PullResultT(NamedTuple):
    addresses: AddressesT
    servers: ServersT


class Local:
    def __init__(
        self,
        docker_watcher: DockerWatcher,
        natmap_monitor_client: Optional[NatmapMonitorClient],
    ) -> None:
        self._docker_watcher = docker_watcher
        self._natmap_monitor_client = natmap_monitor_client

    async def pull(self) -> PullResultT:
        if self._natmap_monitor_client:
            addresses = (
                await self._natmap_monitor_client.get_addresses_filtered_by_config()
            )
        else:
            addresses = AddressesT()

        for address_name, address_info in config.addresses.items():
            if address_info.type == "manual":
                addresses[address_name] = AddressInfoT(
                    type=address_info.params.record_type,
                    host=address_info.params.value,
                    port=address_info.params.port,
                )

        servers = await self._docker_watcher.get_servers()

        return PullResultT(addresses=addresses, servers=servers)
