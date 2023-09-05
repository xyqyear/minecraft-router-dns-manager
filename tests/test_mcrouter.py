from typing import NamedTuple

import pytest

from mc_router_dns_manager.router.mcrouter import AddressNameListT, MCRouter, RoutesT, ServersT
from mc_router_dns_manager.router.mcrouter_client import MCRouterClient


class DummyMCRouterClient(MCRouterClient):
    def __init__(self, base_url: str):
        self._base_url = base_url
        self._routes = RoutesT()

    async def get_routes(self) -> RoutesT:
        return self._routes

    async def override_routes(self, routes: RoutesT):
        self._routes = routes


class RoutesTestPairT(NamedTuple):
    address_name_list: AddressNameListT
    servers: ServersT
    routes: RoutesT


push_test_pairs = [
    RoutesTestPairT(
        address_name_list=["*", "backup", "relay"],
        servers={"vanilla": 25565, "gtnh": 25566},
        routes={
            "vanilla.mc.example.com": "localhost:25565",
            "vanilla.backup.mc.example.com": "localhost:25565",
            "vanilla.relay.mc.example.com": "localhost:25565",
            "gtnh.mc.example.com": "localhost:25566",
            "gtnh.backup.mc.example.com": "localhost:25566",
            "gtnh.relay.mc.example.com": "localhost:25566",
        },
    ),
    RoutesTestPairT(
        address_name_list=["*"],
        servers={"vanilla": 25565},
        routes={"vanilla.mc.example.com": "localhost:25565"},
    ),
    RoutesTestPairT(
        address_name_list=["*", "backup"],
        servers={"vanilla": 25565},
        routes={
            "vanilla.mc.example.com": "localhost:25565",
            "vanilla.backup.mc.example.com": "localhost:25565",
        },
    ),
    RoutesTestPairT(
        address_name_list=["backup"],
        servers={"vanilla": 25565},
        routes={"vanilla.backup.mc.example.com": "localhost:25565"},
    ),
]


@pytest.mark.parametrize("address_name_list, servers, expected_routes", push_test_pairs)
@pytest.mark.asyncio
async def test_push(
    address_name_list: AddressNameListT, servers: ServersT, expected_routes: RoutesT
):
    dummy_router = DummyMCRouterClient("http://localhost:5000")
    mcrouter = MCRouter(dummy_router, "example.com", "mc")

    mcrouter.set_address_name_list(address_name_list)
    mcrouter.set_servers(servers)
    await mcrouter.push()

    routes = await dummy_router.get_routes()
    assert routes == expected_routes


@pytest.mark.parametrize(
    "expected_address_name_list, expected_servers, routes", push_test_pairs
)
@pytest.mark.asyncio
async def test_pull(
    expected_address_name_list: AddressNameListT,
    expected_servers: ServersT,
    routes: RoutesT,
):
    dummy_router = DummyMCRouterClient("http://localhost:5000")
    await dummy_router.override_routes(routes)
    mcrouter = MCRouter(dummy_router, "example.com", "mc")

    await mcrouter.pull()

    assert set(mcrouter.get_address_name_list()) == set(expected_address_name_list)
    assert mcrouter.get_servers() == expected_servers
