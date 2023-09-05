"""
wrapper for mc-router client
"""

from typing import NamedTuple

from .mcrouter_client import BaseMCRouterClient, RoutesT

AddressNameListT = list[str]

# server_list: [server_name, server_port]
ServersT = dict[str, int]


class ParsedServerAddressT(NamedTuple):
    server_name: str
    address_name: str
    server_port: int


class MCRouterPullResultT(NamedTuple):
    address_name_list: AddressNameListT
    servers: ServersT


class MCRouter:
    def __init__(
        self, mc_router_client: BaseMCRouterClient, domain: str, managed_sub_domain: str
    ) -> None:
        self._client = mc_router_client
        self._domain = domain
        self._managed_sub_domain = managed_sub_domain

    async def pull(self) -> MCRouterPullResultT:
        """
        pull routes from mc-router
        :raises Exception: if failed to get routes from mc-router, raised by aiohttp
        """
        routes = await self._client.get_routes()

        address_name_list = AddressNameListT()
        servers = ServersT()
        for server_address, backend in routes.items():
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

            if not address_name in address_name_list:
                address_name_list.append(address_name)
            if not server_name in servers:
                servers[server_name] = server_port

        return MCRouterPullResultT(address_name_list, servers)

    async def push(self, address_name_list: AddressNameListT, servers: ServersT):
        """
        push routes to mc-router
        :raises Exception: if failed to get routes from mc-router, raised by aiohttp
        """
        routes = RoutesT()
        for server_name, server_port in servers.items():
            for address_name in address_name_list:
                if address_name == "*":
                    sub_domain_base = f"{self._managed_sub_domain}"
                else:
                    sub_domain_base = f"{address_name}.{self._managed_sub_domain}"
                routes[
                    f"{server_name}.{sub_domain_base}.{self._domain}"
                ] = f"localhost:{server_port}"

        await self._client.override_routes(routes)
