from typing import NamedTuple

import pytest

from mc_router_dns_manager.dns import (
    AddRecordListT,
    AddRecordT,
    DNSClient,
    RecordIdListT,
    RecordListT,
    ReturnRecordT,
)
from mc_router_dns_manager.mcdns import AddressesT, AddressInfoT, MCDNSClient


class DummyDNSClient(DNSClient):
    def __init__(self, domain: str):
        self._domain = domain
        self._records = dict[int, AddRecordT]()
        self._next_id = 0

    def _get_next_id(self) -> int:
        self._next_id += 1
        return self._next_id

    def get_domain(self) -> str:
        return self._domain

    async def list_records(self) -> RecordListT:
        return [
            ReturnRecordT(
                sub_domain=record.sub_domain,
                value=record.value,
                record_id=record_id,
                record_type=record.record_type,
                ttl=record.ttl,
            )
            for record_id, record in self._records.items()
        ]

    async def update_records_value(self, record_ids: RecordIdListT, value: str):
        ...

    async def remove_records(self, record_ids: RecordIdListT):
        for record_id in record_ids:
            del self._records[record_id]

    async def add_records(self, records: AddRecordListT):
        for record in records:
            record_id = self._get_next_id()
            self._records[record_id] = record


class MCDNSPullTestPairT(NamedTuple):
    record_list: AddRecordListT
    expected_addresses: AddressesT
    expected_server_list: list[str]


class MCDNSPushTestPairT(NamedTuple):
    original_record_list: AddRecordListT
    addresses: AddressesT
    server_list: list[str]
    expected_record_list: AddRecordListT


pull_test_pairs = [
    MCDNSPullTestPairT(
        record_list=[
            AddRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_type="A",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.mc",
                value="0 5 25565 vanilla.mc.example.com.",
                record_type="SRV",
                ttl=600,
            ),
        ],
        expected_addresses=AddressesT(
            {
                "*": AddressInfoT(
                    type="A",
                    host="1.1.1.1",
                    port=25565,
                )
            }
        ),
        expected_server_list=["vanilla"],
    ),
    MCDNSPullTestPairT(
        record_list=[
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
        expected_addresses=AddressesT(
            {
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
            }
        ),
        expected_server_list=["vanilla", "gtnh"],
    ),
]

push_test_pairs = [
    MCDNSPushTestPairT(
        original_record_list=[
            AddRecordT(
                sub_domain="*.mc",
                value="2.2.2.2",
                record_type="A",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.mc",
                value="0 5 25565 vanilla.mc.example.com.",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="*.irrelevant",
                value="example.com.",
                record_type="CNAME",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.irrelevant",
                value="0 5 25565 irrelevant.example.com.",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="mc",
                value="4.4.4.4",
                record_type="A",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="backup.mc",
                value="otherdomain.com.",
                record_type="CNAME",
                ttl=600,
            ),
        ],
        addresses=AddressesT(
            {
                "*": AddressInfoT(
                    type="A",
                    host="1.1.1.1",
                    port=25565,
                )
            }
        ),
        server_list=["vanilla"],
        expected_record_list=[
            AddRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_type="A",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.mc",
                value="0 5 25565 vanilla.mc.example.com.",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="*.irrelevant",
                value="example.com.",
                record_type="CNAME",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.irrelevant",
                value="0 5 25565 irrelevant.example.com.",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="mc",
                value="4.4.4.4",
                record_type="A",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="backup.mc",
                value="otherdomain.com.",
                record_type="CNAME",
                ttl=600,
            ),
        ],
    ),
]

for test_pair in pull_test_pairs:
    push_test_pairs.append(
        MCDNSPushTestPairT(
            original_record_list=[],
            addresses=test_pair.expected_addresses,
            server_list=test_pair.expected_server_list,
            expected_record_list=test_pair.record_list,
        )
    )


@pytest.mark.parametrize(
    "record_list, expected_addresses, expected_server_list", pull_test_pairs
)
@pytest.mark.asyncio
async def test_pull(
    record_list: AddRecordListT,
    expected_addresses: AddressesT,
    expected_server_list: list[str],
):
    dns_client = DummyDNSClient("example.com")
    await dns_client.add_records(record_list)

    mcdns = MCDNSClient(dns_client, "mc")
    await mcdns.pull()

    assert mcdns.get_addresses() == expected_addresses
    assert set(mcdns.get_server_list()) == set(expected_server_list)


@pytest.mark.parametrize(
    "original_record_list, addresses, server_list, expected_record_list",
    push_test_pairs,
)
@pytest.mark.asyncio
async def test_push(
    original_record_list: AddRecordListT,
    addresses: AddressesT,
    server_list: list[str],
    expected_record_list: AddRecordListT,
):
    dns_client = DummyDNSClient("example.com")
    await dns_client.add_records(original_record_list)

    mcdns = MCDNSClient(dns_client, "mc")
    mcdns.set_addresses(addresses)
    mcdns.set_server_list(server_list)
    await mcdns.push()

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
