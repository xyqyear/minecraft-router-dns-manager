"""
wrapper for mc-router client
"""

from .mcrouter_client import MCRouterClient
from typing import NamedTuple
from .mcrouter_client import RoutesT

AddressNameListT = list[str]

# server_list: [server_name, server_port]
ServersT = dict[str, int]


class ParsedServerAddressT(NamedTuple):
    server_name: str
    address_name: str
    server_port: int


class MCRouter:
    def __init__(self, base_url: str, domain: str, managed_sub_domain: str) -> None:
        self._client = MCRouterClient(base_url)
        self._domain = domain
        self._managed_sub_domain = managed_sub_domain

        self._address_name_list = AddressNameListT()
        self._servers = ServersT()

    def _from_routes(self, routes: RoutesT):
        """
        parse server_address to server_name and server_port
        """
        self._address_name_list.clear()
        self._servers.clear()

        for server_address, backend in routes.items():
            # parse
            if ":" in backend:
                _, server_port = backend.split(":")
                server_port = int(server_port)
            else:
                server_port = 25565

            server_and_address = server_address.split(
                f".{self._managed_sub_domain}.{self._domain}"
            )[0].split(".")
            server_name = server_and_address[0]
            if len(server_and_address) == 1:
                address_name = "*"
            else:
                address_name = server_and_address[1]

            # update self
            if not address_name in self._address_name_list:
                self._address_name_list.append(address_name)
            if not server_name in self._servers:
                self._servers[server_name] = server_port

    def _to_routes(self) -> RoutesT:
        """
        construct routes from self._servers
        """
        routes = RoutesT()
        for server_name, server_port in self._servers.items():
            for address_name in self._address_name_list:
                if address_name == "*":
                    sub_domain_base = f"{self._managed_sub_domain}"
                else:
                    sub_domain_base = f"{address_name}.{self._managed_sub_domain}"
                routes[
                    f"{server_name}.{sub_domain_base}.{self._domain}"
                ] = f"localhost:{server_port}"
        return routes

    async def pull(self):
        """
        pull routes from mc-router
        :raises Exception: if failed to get routes from mc-router, raised by aiohttp
        """
        routes = await self._client.get_all_routes()
        self._from_routes(routes)

    async def push(self):
        """
        push routes to mc-router
        :raises Exception: if failed to get routes from mc-router, raised by aiohttp
        """
        new_routes = self._to_routes()
        await self._client.override_routes(new_routes)

    def get_address_name_list(self) -> AddressNameListT:
        """
        get address name list
        """
        return self._address_name_list

    def set_address_name_list(self, address_name_list: AddressNameListT):
        """
        set address name list
        """
        self._address_name_list = address_name_list

    def get_servers(self) -> ServersT:
        """
        get servers
        """
        return self._servers

    def set_servers(self, servers: ServersT):
        """
        set servers
        """
        self._servers = servers
