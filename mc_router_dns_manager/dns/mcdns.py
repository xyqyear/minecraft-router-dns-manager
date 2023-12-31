import asyncio
from typing import Literal, NamedTuple, Optional

from ..logger import logger
from .dns import AddRecordListT, AddRecordT, DNSClient, RecordListT, ReturnRecordT


class AddressInfoT(NamedTuple):
    type: Literal["A", "AAAA", "CNAME"]
    host: str
    port: int


AddressesT = dict[str, AddressInfoT]


class SrvParsedResultT(NamedTuple):
    server_name: str
    address_name: str
    port: int


class MCDNSPullResultT(NamedTuple):
    addresses: AddressesT
    server_list: list[str]


"""
as for the `sub_domain` confusion,

the `sub_domain` in the `AddRecordT` is the record name
    for example, if we want to add a record for `backup.mc.example.com`,
    then the `sub_domain` should be `backup.mc`
    this is inherited from dnspod api

the `managed_sub_domain` in the `MCDNSClient` is the sub domain we want to manage
    for example, if we want to manage the sub domain `mc.example.com`,
    then the `managed_sub_domain` should be `mc`

the `sub_domain_base` in the `MCDNSClient._generate_records` is the sub domain base for the record
    for example, if we want to add a srv record `_minecraft._tcp.vanilla.backup.mc.example.com`,
    then the `sub_domain_base` should be `backup.mc`

the `address_name` is another whole mess
    suppose you have two ip and port pairs for the server,
    one is the main address, the other is the backup address
    then the `address_name` for the main address should be `*`, so that the srv record will be `_minecraft._tcp.vanilla.mc.example.com`
    and the `address_name` for the backup address could be `backup`, so that the srv record will be `_minecraft._tcp.vanilla.backup.mc.example.com`

"""


class MCDNS:
    def __init__(
        self, dns_client: DNSClient, managed_sub_domain: str, dns_ttl: int = 600
    ):
        self._dns_client = dns_client
        self._managed_sub_domain = managed_sub_domain
        self._dns_ttl = dns_ttl

        self._dns_update_lock = asyncio.Lock()

    async def _get_relevent_records(self) -> RecordListT:
        record_list = await self._dns_client.list_records()
        relevent_records = RecordListT()
        for record in record_list:
            if (
                record.record_type
                in (
                    "A",
                    "AAAA",
                    "CNAME",
                )
                and record.sub_domain.startswith("*")
                and record.sub_domain.endswith(f".{self._managed_sub_domain}")
            ):
                relevent_records.append(record)
            elif (
                record.record_type == "SRV"
                and record.sub_domain.startswith(f"_minecraft._tcp.")
                and record.sub_domain.endswith(f".{self._managed_sub_domain}")
            ):
                relevent_records.append(record)
        return relevent_records

    async def _remove_relevent_records(self):
        records = await self._get_relevent_records()
        record_ids = [record.record_id for record in records]
        if record_ids:
            await self._dns_client.remove_records(record_ids)

    def set_dns_client(self, dns_client: DNSClient):
        """
        only sets the internal dns client, does not push or pull
        for test or migration purposes
        """
        self._dns_client = dns_client

    def set_ttl(self, ttl: int):
        self._dns_ttl = ttl

    def _parse_srv_record(self, record: ReturnRecordT) -> SrvParsedResultT:
        """
        parse the srv record value to a tuple of (target, port)
        """
        _, _, port, server_host = record.value.split(" ")
        full_sub_domain = server_host.split(
            f".{self._managed_sub_domain}.{self._dns_client.get_domain()}"
        )[0]
        if "." in full_sub_domain:
            server_name, address_name = full_sub_domain.split(".")
        else:
            server_name, address_name = full_sub_domain, "*"

        return SrvParsedResultT(
            server_name=server_name, address_name=address_name, port=int(port)
        )

    async def pull(self) -> Optional[MCDNSPullResultT]:
        """
        pull the address list from the dns record
        :raises Exception: if failed to get records from dns client
        """
        if not self._dns_client.is_initialized():
            await self._dns_client.init()
        record_list = await self._get_relevent_records()

        addresses = AddressesT()
        # we use a dict of lists instead of a simple server name list
        # to check the consistency of the srv records
        # because sometimes the dns provider doesn't update the records correctly
        # I'm looking at you, dnspod.
        server_to_addresses_list_map = dict[str, list[str]]()

        port_map = dict[str, int]()
        for record in record_list:
            if record.record_type == "SRV":
                parsed_result = self._parse_srv_record(record)
                port_map[parsed_result.address_name] = parsed_result.port
                server_to_addresses_list_map.setdefault(
                    parsed_result.server_name, []
                ).append(parsed_result.address_name)
            # if it's not a srv record, then it must be a A/AAAA/CNAME record
            # we do this to just make pylance happy
            elif record.record_type in ("A", "AAAA", "CNAME"):
                splitted_sub_domain = record.sub_domain.split(".")
                if len(splitted_sub_domain) < 2:
                    return None
                address_name = splitted_sub_domain[-2]
                addresses[address_name] = AddressInfoT(
                    type=record.record_type,
                    host=record.value,
                    port=0,
                )

        # check if the srv records are consistent
        # if not, return None
        for _, addresses_list in server_to_addresses_list_map.items():
            if set(addresses_list) != set(addresses.keys()):
                logger.info(
                    f"srv records are not consistent: {server_to_addresses_list_map}"
                )
                return None

        for address_name in addresses.keys():
            if address_name in port_map:
                addresses[address_name] = addresses[address_name]._replace(
                    port=port_map[address_name]
                )
            else:
                return None

        server_list = list(server_to_addresses_list_map.keys())

        return MCDNSPullResultT(addresses, server_list)

    async def push(self, addresses: AddressesT, server_list: list[str]):
        """
        sync the dns record to the address list
        :raises Exception: if failed to update dns record
        """
        if not (addresses and server_list):
            logger.warning(
                "addresses or server_list is empty, deleting all relevant records"
            )
            await self._remove_relevent_records()
            return

        record_list = AddRecordListT()
        for address_name, address_info in addresses.items():
            if address_name == "*":
                sub_domain_base = f"{self._managed_sub_domain}"
            else:
                sub_domain_base = f"{address_name}.{self._managed_sub_domain}"
            record_list.append(
                AddRecordT(
                    sub_domain=f"*.{sub_domain_base}",
                    value=address_info.host,
                    record_type=address_info.type,
                    ttl=self._dns_ttl,
                )
            )
            for server_name in server_list:
                record_list.append(
                    AddRecordT(
                        sub_domain=f"_minecraft._tcp.{server_name}.{sub_domain_base}",
                        value=f"0 5 {address_info.port} {server_name}.{sub_domain_base}.{self._dns_client.get_domain()}",
                        record_type="SRV",
                        ttl=self._dns_ttl,
                    )
                )

        # we want to make sure only one push is running at the same time
        async with self._dns_update_lock:
            await self._remove_relevent_records()
            logger.info(f"adding records: {record_list}")
            await self._dns_client.add_records(record_list)
