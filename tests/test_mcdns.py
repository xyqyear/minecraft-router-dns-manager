from typing import NamedTuple

import pytest

from mc_router_dns_manager.dns.dns import (
    AddRecordListT,
    AddRecordT,
    DNSClient,
    RecordIdListT,
    RecordListT,
    ReturnRecordT,
)
from mc_router_dns_manager.dns.mcdns import (
    MCDNS,
    AddressesT,
    AddressInfoT,
    DiffUpdateRecordResultT,
)


class DummyDNSClient(DNSClient):
    def __init__(self, domain: str, has_update_capability: bool = True):
        self._domain = domain
        self._records = dict[int | str, AddRecordT]()
        self._next_id = 0
        self._has_update_capability_value = has_update_capability

    def is_initialized(self) -> bool:
        return True

    def _get_next_id(self) -> int:
        self._next_id += 1
        return self._next_id

    def get_domain(self) -> str:
        return self._domain

    def has_update_capability(self) -> bool:
        return self._has_update_capability_value

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

    async def update_records(self, records: RecordListT):
        for record in records:
            self._records[record.record_id] = AddRecordT(
                sub_domain=record.sub_domain,
                value=record.value,
                record_type=record.record_type,
                ttl=record.ttl,
            )

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


common_test_pairs = [
    MCDNSPullTestPairT(
        record_list=[],
        expected_addresses=AddressesT({}),
        expected_server_list=[],
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
                sub_domain="_minecraft._tcp.vanilla.mc",
                value="0 5 25565 vanilla.mc.example.com",
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
                value="domain2.com",
                record_type="CNAME",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="*.hk.mc",
                value="domain3.com",
                record_type="CNAME",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.mc",
                value="0 5 11111 vanilla.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.backup.mc",
                value="0 5 22222 vanilla.backup.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.hk.mc",
                value="0 5 33333 vanilla.hk.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.gtnh.mc",
                value="0 5 11111 gtnh.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.gtnh.backup.mc",
                value="0 5 22222 gtnh.backup.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.gtnh.hk.mc",
                value="0 5 33333 gtnh.hk.mc.example.com",
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
                    host="domain2.com",
                    port=22222,
                ),
                "hk": AddressInfoT(
                    type="CNAME",
                    host="domain3.com",
                    port=33333,
                ),
            }
        ),
        expected_server_list=["vanilla", "gtnh"],
    ),
]

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
                sub_domain="*.backup.mc",
                value="domain2.com",
                record_type="CNAME",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="*.hk.mc",
                value="domain3.com",
                record_type="CNAME",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.mc",
                value="0 5 11111 vanilla.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.backup.mc",
                value="0 5 22222 vanilla.backup.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.hk.mc",
                value="0 5 33333 vanilla.hk.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.gtnh.backup.mc",
                value="0 5 22222 gtnh.backup.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.gtnh.hk.mc",
                value="0 5 33333 gtnh.hk.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
        ],
        expected_addresses=AddressesT({}),
        expected_server_list=[],
    ),
    MCDNSPullTestPairT(
        record_list=[
            AddRecordT(
                sub_domain="mc",
                value="1.1.1.1",
                record_type="A",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.vanilla.mc",
                value="0 5 25565 vanilla.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
        ],
        expected_addresses=AddressesT({}),
        expected_server_list=[],
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
                value="0 5 25565 vanilla.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="*.irrelevant",
                value="example.com",
                record_type="CNAME",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.irrelevant",
                value="0 5 25565 irrelevant.example.com",
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
                value="otherdomain.com",
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
                value="0 5 25565 vanilla.mc.example.com",
                record_type="SRV",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="*.irrelevant",
                value="example.com",
                record_type="CNAME",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="_minecraft._tcp.irrelevant",
                value="0 5 25565 irrelevant.example.com",
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
                value="otherdomain.com",
                record_type="CNAME",
                ttl=600,
            ),
        ],
    ),
]

pull_test_pairs.extend(common_test_pairs)

for test_pair in common_test_pairs:
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
async def test_pull(
    record_list: AddRecordListT,
    expected_addresses: AddressesT,
    expected_server_list: list[str],
):
    dns_client = DummyDNSClient("example.com")
    await dns_client.add_records(record_list)

    mcdns = MCDNS(dns_client, "mc")

    pull_result = await mcdns.pull()
    if not pull_result:
        assert expected_addresses == {}
        return

    pulled_addresses, pulled_server_list = pull_result

    assert pulled_addresses == expected_addresses
    assert set(pulled_server_list) == set(expected_server_list)


@pytest.mark.parametrize(
    "original_record_list, addresses, server_list, expected_record_list",
    push_test_pairs,
)
async def test_push(
    original_record_list: AddRecordListT,
    addresses: AddressesT,
    server_list: list[str],
    expected_record_list: AddRecordListT,
):
    for has_update_capability in [True, False]:
        dns_client = DummyDNSClient("example.com", has_update_capability)
        await dns_client.add_records(original_record_list)

        mcdns = MCDNS(dns_client, "mc")
        await mcdns.push(addresses, server_list)

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


class MCDNSDiffUpdateRecordsTestPairT(NamedTuple):
    old_records: RecordListT
    new_records: AddRecordListT
    expected_return: DiffUpdateRecordResultT


diff_update_records_test_pairs = [
    # test empty old and new records
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[],
        new_records=[],
        expected_return=DiffUpdateRecordResultT([], [], []),
    ),
    # test add new records
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[],
        new_records=[
            AddRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_type="A",
                ttl=600,
            ),
        ],
        expected_return=DiffUpdateRecordResultT(
            [
                AddRecordT(
                    sub_domain="*.mc",
                    value="1.1.1.1",
                    record_type="A",
                    ttl=600,
                )
            ],
            [],
            [],
        ),
    ),
    # test remove old records
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[
            ReturnRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_id=1,
                record_type="A",
                ttl=600,
            ),
        ],
        new_records=[],
        expected_return=DiffUpdateRecordResultT(
            [],
            [1],
            [],
        ),
    ),
    # test update records
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[
            ReturnRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_id=1,
                record_type="A",
                ttl=600,
            ),
        ],
        new_records=[
            AddRecordT(
                sub_domain="*.mc",
                value="1.1.1.2",
                record_type="A",
                ttl=600,
            ),
        ],
        expected_return=DiffUpdateRecordResultT(
            [],
            [],
            [
                ReturnRecordT(
                    sub_domain="*.mc",
                    value="1.1.1.2",
                    record_id=1,
                    record_type="A",
                    ttl=600,
                )
            ],
        ),
    ),
    # test identical records
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[
            ReturnRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_id=1,
                record_type="A",
                ttl=600,
            ),
        ],
        new_records=[
            AddRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_type="A",
                ttl=600,
            ),
        ],
        expected_return=DiffUpdateRecordResultT([], [], []),
    ),
    # test different TTL
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[
            ReturnRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_id=1,
                record_type="A",
                ttl=600,
            ),
        ],
        new_records=[
            AddRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_type="A",
                ttl=300,
            ),
        ],
        expected_return=DiffUpdateRecordResultT(
            [],
            [],
            [
                ReturnRecordT(
                    sub_domain="*.mc",
                    value="1.1.1.1",
                    record_id=1,
                    record_type="A",
                    ttl=300,
                )
            ],
        ),
    ),
    # test different value and TTL
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[
            ReturnRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_id=1,
                record_type="A",
                ttl=600,
            ),
        ],
        new_records=[
            AddRecordT(
                sub_domain="*.mc",
                value="1.1.1.2",
                record_type="A",
                ttl=300,
            ),
        ],
        expected_return=DiffUpdateRecordResultT(
            [],
            [],
            [
                ReturnRecordT(
                    sub_domain="*.mc",
                    value="1.1.1.2",
                    record_id=1,
                    record_type="A",
                    ttl=300,
                )
            ],
        ),
    ),
    # test add new record and update existing record
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[
            ReturnRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_id=1,
                record_type="A",
                ttl=600,
            ),
        ],
        new_records=[
            AddRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_type="A",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="test.mc",
                value="2.2.2.2",
                record_type="A",
                ttl=600,
            ),
        ],
        expected_return=DiffUpdateRecordResultT(
            [
                AddRecordT(
                    sub_domain="test.mc",
                    value="2.2.2.2",
                    record_type="A",
                    ttl=600,
                )
            ],
            [],
            [],
        ),
    ),
    # test remove record and add new record
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[
            ReturnRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_id=1,
                record_type="A",
                ttl=600,
            ),
        ],
        new_records=[
            AddRecordT(
                sub_domain="test.mc",
                value="2.2.2.2",
                record_type="A",
                ttl=600,
            ),
        ],
        expected_return=DiffUpdateRecordResultT(
            [
                AddRecordT(
                    sub_domain="test.mc",
                    value="2.2.2.2",
                    record_type="A",
                    ttl=600,
                )
            ],
            [1],
            [],
        ),
    ),
    # test update multiple records
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[
            ReturnRecordT(
                sub_domain="*.mc",
                value="1.1.1.1",
                record_id=1,
                record_type="A",
                ttl=600,
            ),
            ReturnRecordT(
                sub_domain="test.mc",
                value="2.2.2.2",
                record_id=2,
                record_type="A",
                ttl=300,
            ),
        ],
        new_records=[
            AddRecordT(
                sub_domain="*.mc",
                value="1.1.1.2",
                record_type="A",
                ttl=600,
            ),
            AddRecordT(
                sub_domain="test.mc",
                value="2.2.2.3",
                record_type="A",
                ttl=300,
            ),
        ],
        expected_return=DiffUpdateRecordResultT(
            [],
            [],
            [
                ReturnRecordT(
                    sub_domain="*.mc",
                    value="1.1.1.2",
                    record_id=1,
                    record_type="A",
                    ttl=600,
                ),
                ReturnRecordT(
                    sub_domain="test.mc",
                    value="2.2.2.3",
                    record_id=2,
                    record_type="A",
                    ttl=300,
                ),
            ],
        ),
    ),
    # test empty sub_domain
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[
            ReturnRecordT(
                sub_domain="",
                value="3.3.3.3",
                record_id=3,
                record_type="A",
                ttl=600,
            ),
        ],
        new_records=[
            AddRecordT(
                sub_domain="",
                value="4.4.4.4",
                record_type="A",
                ttl=600,
            ),
        ],
        expected_return=DiffUpdateRecordResultT(
            [],
            [],
            [
                ReturnRecordT(
                    sub_domain="",
                    value="4.4.4.4",
                    record_id=3,
                    record_type="A",
                    ttl=600,
                )
            ],
        ),
    ),
    # test multiple changes with different TTLs and values
    MCDNSDiffUpdateRecordsTestPairT(
        old_records=[
            ReturnRecordT(
                sub_domain="a.mc",
                value="5.5.5.5",
                record_id=4,
                record_type="A",
                ttl=600,
            ),
            ReturnRecordT(
                sub_domain="b.mc",
                value="6.6.6.6",
                record_id=5,
                record_type="A",
                ttl=300,
            ),
        ],
        new_records=[
            AddRecordT(
                sub_domain="a.mc",
                value="5.5.5.6",
                record_type="A",
                ttl=700,
            ),
            AddRecordT(
                sub_domain="b.mc",
                value="6.6.6.7",
                record_type="A",
                ttl=400,
            ),
        ],
        expected_return=DiffUpdateRecordResultT(
            [],
            [],
            [
                ReturnRecordT(
                    sub_domain="a.mc",
                    value="5.5.5.6",
                    record_id=4,
                    record_type="A",
                    ttl=700,
                ),
                ReturnRecordT(
                    sub_domain="b.mc",
                    value="6.6.6.7",
                    record_id=5,
                    record_type="A",
                    ttl=400,
                ),
            ],
        ),
    ),
]


@pytest.mark.parametrize(
    "old_records, new_records, expected_return", diff_update_records_test_pairs
)
async def test_diff_update_records(
    old_records: RecordListT,
    new_records: AddRecordListT,
    expected_return: DiffUpdateRecordResultT,
):
    assert expected_return == MCDNS._diff_update_records(old_records, new_records)  # type: ignore since we are unit testing
