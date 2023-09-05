"""
Responsibility: update mc-router and dns records with relevant information
"""
import asyncio

from .mcdns import MCDNS, AddressesT
from .mcrouter import MCRouter, ServersT


class Updater:
    def __init__(self, mc_router: MCRouter, mc_dns: MCDNS) -> None:
        self._mc_router = mc_router
        self._mc_dns = mc_dns

    async def push(self, addresses: AddressesT, servers: ServersT):
        self._mc_dns.set_addresses(addresses)
        self._mc_dns.set_server_list(list(servers.keys()))

        self._mc_router.set_address_name_list(list(addresses.keys()))
        self._mc_router.set_servers(servers)

        await asyncio.gather(self._mc_router.push(), self._mc_dns.push())
