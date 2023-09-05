from typing import NamedTuple

import pytest

from mc_router_dns_manager.mcrouter import AddressNameListT, MCRouter, RoutesT, ServersT


class RoutesTestPairT(NamedTuple):
    address_name_list: AddressNameListT
    servers: ServersT
    routes: RoutesT


to_routes_test_pairs = [
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


@pytest.mark.parametrize(
    "address_name_list, servers, expected_routes", to_routes_test_pairs
)
@pytest.mark.asyncio
async def test_to_routes(
    address_name_list: AddressNameListT, servers: ServersT, expected_routes: RoutesT
):
    mcrouter = MCRouter("http://localhost:5000", "example.com", "mc")

    mcrouter.set_address_name_list(address_name_list)
    mcrouter.set_servers(servers)

    routes = mcrouter._to_routes()  # type: ignore
    assert routes == expected_routes


@pytest.mark.parametrize(
    "expected_address_name_list, expected_servers, routes", to_routes_test_pairs
)
@pytest.mark.asyncio
async def test_from_routes(
    expected_address_name_list: AddressNameListT,
    expected_servers: ServersT,
    routes: RoutesT,
):
    mcrouter = MCRouter("http://localhost:5000", "example.com", "mc")

    mcrouter._from_routes(routes)  # type: ignore

    assert set(mcrouter.get_address_name_list()) == set(expected_address_name_list)
    assert mcrouter.get_servers() == expected_servers
