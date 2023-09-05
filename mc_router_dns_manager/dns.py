from typing import NamedTuple

RecordIdT = int
RecordIdListT = list[RecordIdT]


class ReturnRecordT(NamedTuple):
    sub_domain: str
    value: str
    record_id: int
    record_type: str
    ttl: int


class AddRecordT(NamedTuple):
    sub_domain: str
    value: str
    record_type: str
    ttl: int


RecordListT = list[ReturnRecordT]
AddRecordListT = list[AddRecordT]


class DNSClient:
    """
    abstract class for dns client
    """

    def get_domain(self) -> str:
        ...

    async def list_records(self) -> RecordListT:
        ...

    async def update_records_value(self, record_ids: RecordIdListT, value: str):
        ...

    async def remove_records(self, record_ids: RecordIdListT):
        ...

    async def add_records(self, records: AddRecordListT):
        ...
