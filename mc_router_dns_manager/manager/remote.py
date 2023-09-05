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
        self._mc_dns.set_addresses(addresses)
        self._mc_dns.set_server_list(list(servers.keys()))

        self._mc_router.set_address_name_list(list(addresses.keys()))
        self._mc_router.set_servers(servers)

        await asyncio.gather(self._mc_router.push(), self._mc_dns.push())

    async def pull(self) -> Optional[PullResultT]:
        """
        if dns record isn't consistent with mc-router, return None
        """
        await asyncio.gather(self._mc_router.pull(), self._mc_dns.pull())

        addresses = self._mc_dns.get_addresses()
        server_list = self._mc_dns.get_server_list()
        address_list = self._mc_router.get_address_name_list()
        servers = self._mc_router.get_servers()

        if set(address_list) != set(addresses.keys()):
            return None

        if set(server_list) != set(servers.keys()):
            return None

        return PullResultT(addresses, servers)
