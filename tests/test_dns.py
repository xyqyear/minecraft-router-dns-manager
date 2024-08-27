import os
from typing import cast

import pytest
from dotenv import dotenv_values

from mc_router_dns_manager.dns.dns import (
    AddRecordListT,
    AddRecordT,
    RecordListT,
    ReturnRecordT,
)
from mc_router_dns_manager.dns.huawei import HuaweiDNSClient

add_test_record_list = [
    [AddRecordT(sub_domain="add1", value="1.1.1.1", record_type="A", ttl=600)],
    [AddRecordT(sub_domain="add2", value="example.com", record_type="CNAME", ttl=600)],
    [
        AddRecordT(
            sub_domain="add3", value="0 5 80 example.com", record_type="SRV", ttl=600
        )
    ],
    [AddRecordT(sub_domain="add4", value="f::", record_type="AAAA", ttl=600)],
]
add_test_record_list.append(sum(add_test_record_list, start=list[AddRecordT]()))

update_test_record_list = [
    [
        [
            AddRecordT(sub_domain="update1", value="1.1.1.1", record_type="A", ttl=600),
            "2.2.2.2",
        ],
    ],
    [
        [
            AddRecordT(
                sub_domain="update2", value="example.com", record_type="CNAME", ttl=600
            ),
            "example2.com",
        ],
    ],
    [
        [
            AddRecordT(
                sub_domain="update3",
                value="0 5 80 example.com",
                record_type="SRV",
                ttl=600,
            ),
            "0 5 80 example2.com",
        ],
    ],
    [
        [
            AddRecordT(sub_domain="update4", value="f::", record_type="AAAA", ttl=600),
            "f::1",
        ],
    ],
]
update_test_record_list.append(
    sum(update_test_record_list, start=list[list[AddRecordT | str]]())
)


def record_list_to_add_record_list(record_list: RecordListT) -> AddRecordListT:
    return [
        AddRecordT(
            sub_domain=record.sub_domain,
            value=record.value,
            record_type=record.record_type,
            ttl=record.ttl,
        )
        for record in record_list
    ]


def find_record_from_record_list(
    record_list: RecordListT, search_record: AddRecordListT
) -> RecordListT:
    search_table = {
        (record.sub_domain, record.record_type): record for record in record_list
    }
    return_list = RecordListT()
    for record in search_record:
        key = (record.sub_domain, record.record_type)
        if key in search_table:
            return_list.append(search_table[key])

    return return_list


def get_updated_record_list(
    record_list: RecordListT, records_to_update: list[list[AddRecordT | str]]
) -> RecordListT:
    search_table = {
        (record.sub_domain, record.record_type): record for record in record_list
    }
    return_list = RecordListT()
    for record in records_to_update:
        record_to_search = cast(AddRecordT, record[0])
        key = (
            record_to_search.sub_domain,
            record_to_search.record_type,
        )
        if key in search_table:
            found_record = search_table[key]
            return_list.append(
                ReturnRecordT(
                    sub_domain=found_record.sub_domain,
                    value=cast(str, record[1]),
                    record_id=found_record.record_id,
                    record_type=found_record.record_type,
                    ttl=found_record.ttl,
                ),
            )

    return return_list


@pytest.fixture(scope="module")
async def client():
    env_config = dotenv_values(".env")
    test_env_config = dotenv_values(".env.test")

    test_env_config = {
        **env_config,
        **test_env_config,
        **os.environ,
    }

    DOMAIN = test_env_config.get("HUAWEI_DOMAIN")
    assert DOMAIN is not None
    AK = test_env_config.get("HUAWEI_AK")
    assert AK is not None
    SK = test_env_config.get("HUAWEI_SK")
    assert SK is not None

    client = HuaweiDNSClient(DOMAIN, AK, SK)
    await client.init()

    return client


@pytest.mark.parametrize(
    "records",
    add_test_record_list,
)
async def test_list_add_remove_records(
    records: AddRecordListT, client: HuaweiDNSClient
):
    async with client.lock:
        record_list_before_adding = await client.list_records()

        await client.add_records(records)
        record_list_after_adding = await client.list_records()
        added_records = find_record_from_record_list(record_list_after_adding, records)
        assert set(record_list_to_add_record_list(added_records)) == set(records)

        record_ids = [record.record_id for record in added_records]
        await client.remove_records(record_ids)
        record_list_after_removing = await client.list_records()

        assert set(record_list_before_adding) == set(record_list_after_removing)


@pytest.mark.parametrize(
    "records",
    update_test_record_list,
)
async def test_list_add_update_remove_records(
    records: list[list[AddRecordT | str]], client: HuaweiDNSClient
):
    async with client.lock:
        record_list_before_adding = await client.list_records()
        records_to_add = cast(list[AddRecordT], [record[0] for record in records])
        await client.add_records(records_to_add)
        added_records = find_record_from_record_list(
            await client.list_records(), records_to_add
        )
        expected_updated_records = get_updated_record_list(added_records, records)
        await client.update_records(expected_updated_records)

        record_list_after_updating = await client.list_records()
        updated_records = find_record_from_record_list(
            record_list_after_updating, records_to_add
        )

        assert set(updated_records) == set(expected_updated_records)

        record_ids = [record.record_id for record in updated_records]
        await client.remove_records(record_ids)
        record_list_after_removing = await client.list_records()

        assert set(record_list_before_adding) == set(record_list_after_removing)
