from typing import NamedTuple

import pytest

from mc_router_dns_manager.dns.mcdns import (
    MCDNS,
    AddRecordListT,
    AddRecordT,
    AddressesT,
    AddressInfoT,
)
from mc_router_dns_manager.router.mcrouter import MCRouter, RoutesT, ServersT
from mc_router_dns_manager.updater import Updater

from .test_mcdns import DummyDNSClient
from .test_mcrouter import DummyMCRouterClient


class UpdaterTestPairT(NamedTuple):
    addresses: AddressesT
    servers: ServersT
    expected_routes: RoutesT
    expected_record_list: AddRecordListT


updater_test_pairs = [
    UpdaterTestPairT(
        addresses={
            "*": AddressInfoT(
                type="A",
                host="1.1.1.1",
                port=11111,
            ),
            "backup": AddressInfoT(
                type="CNAME",
                host="domain2.com.",
                port=22222,
            ),
            "hk": AddressInfoT(
                type="CNAME",
                host="domain3.com.",
                port=33333,
            ),
        },
        servers={
            "vanilla": 25565,
            "gtnh": 25566,
        },
        expected_routes={
            "vanilla.mc.example.com": "localhost:25565",
            "vanilla.backup.mc.example.com": "localhost:25565",
            "vanilla.hk.mc.example.com": "localhost:25565",
            "gtnh.mc.example.com": "localhost:25566",
            "gtnh.backup.mc.example.com": "localhost:25566",
            "gtnh.hk.mc.example.com": "localhost:25566",
        },
        expected_record_list=[
            AddRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_type="A",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="*.backup.mc",
                value="domain2.com.",
                record_type="CNAME",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="*.hk.mc",
                value="domain3.com.",
                record_type="CNAME",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.mc",
                value="0 5 11111 vanilla.mc.example.com.",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.backup.mc",
                value="0 5 22222 vanilla.backup.mc.example.com.",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.hk.mc",
                value="0 5 33333 vanilla.hk.mc.example.com.",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.gtnh.mc",
                value="0 5 11111 gtnh.mc.example.com.",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.gtnh.backup.mc",
                value="0 5 22222 gtnh.backup.mc.example.com.",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.gtnh.hk.mc",
                value="0 5 33333 gtnh.hk.mc.example.com.",
                record_type="SRV",
                ttl=600,
            ),
        ],
    )
]


@pytest.mark.parametrize(
    "addresses, servers, expected_routes, expected_record_list", updater_test_pairs
)
@pytest.mark.asyncio
async def test_push(
    addresses: AddressesT,
    servers: ServersT,
    expected_routes: RoutesT,
    expected_record_list: AddRecordListT,
):
    dns_client = DummyDNSClient("example.com")

    mc_router_client = DummyMCRouterClient("http://localhost:5000")

    updater = Updater(
        MCRouter(mc_router_client, "example.com", "mc"), MCDNS(dns_client, "mc")
    )
    await updater.push(addresses, servers)

    record_list = await dns_client.list_records()
    record_list_with_out_id = [
        AddRecordT(
            sub_domain=record.sub_domain,
            value=record.value,
            record_type=record.record_type,
            ttl=record.ttl,
        )
        for record in record_list
    ]
    assert set(record_list_with_out_id) == set(expected_record_list)

    routes = await mc_router_client.get_routes()
    assert routes == expected_routes
