"""
Responsibility: update mc-router and dns records with relevant information
"""
import asyncio
from typing import NamedTuple, Optional

from ..dns.mcdns import MCDNS, AddressesT
from ..router.mcrouter import MCRouter, ServersT


class PullResultT(NamedTuple):
    addresses: AddressesT
    servers: ServersT


class Remote:
    def __init__(self, mc_router: MCRouter, mc_dns: MCDNS) -> None:
        self._mc_router = mc_router
        self._mc_dns = mc_dns

    async def push(self, addresses: AddressesT, servers: ServersT):
        await asyncio.gather(
            self._mc_router.push(list(addresses.keys()), servers),
            self._mc_dns.push(addresses, list(servers.keys())),
        )

    async def pull(self) -> Optional[PullResultT]:
        """
        if dns record isn't consistent with mc-router, return None
        """
        (address_list, servers), mcdns_pull_result = await asyncio.gather(
            self._mc_router.pull(), self._mc_dns.pull()
        )

        if not mcdns_pull_result:
            return None

        (addresses, server_list) = mcdns_pull_result

        if set(address_list) != set(addresses.keys()):
            return None

        if set(server_list) != set(servers.keys()):
            return None

        return PullResultT(addresses, servers)
