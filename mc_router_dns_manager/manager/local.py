"""
Responsibility: update mc-router and dns records with relevant information
"""
from typing import NamedTuple, Optional, cast

from ..client.docker_watcher_client import DockerWatcherClient
from ..client.natmap_monitor_client import NatmapMonitorClient
from ..config import ManualParamsT, config
from ..dns.mcdns import AddressesT, AddressInfoT
from ..router.mcrouter import ServersT


class PullResultT(NamedTuple):
    addresses: AddressesT
    servers: ServersT


class Local:
    def __init__(
        self,
        docker_watcher: DockerWatcherClient,
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

        for address_name, address_info in config["addresses"].items():
            if address_info["type"] == "manual":
                address_params = cast(ManualParamsT, address_info["params"])
                addresses[address_name] = AddressInfoT(
                    type=address_params["record_type"],
                    host=address_params["value"],
                    port=address_params["port"],
                )

        servers = await self._docker_watcher.get_servers()

        return PullResultT(addresses=addresses, servers=servers)
