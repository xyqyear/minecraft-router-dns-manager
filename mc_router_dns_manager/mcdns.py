from .dns import DNSClient, ReturnRecordT, RecordListT, AddRecordListT, AddRecordT
from typing import TypedDict, Literal
import asyncio


class AddressInfoT(TypedDict):
    type: Literal["A", "AAAA", "CNAME"]
    host: str
    port: int


AddressesT = dict[str, AddressInfoT]


class SrvParsedResultT(TypedDict):
    server_name: str
    address_name: str
    port: int


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


class MCDNSClient:
    def __init__(self, dns_client: DNSClient, managed_sub_domain: str):
        self._dns_client = dns_client
        self._managed_sub_domain = managed_sub_domain
        self._addresses = AddressesT()
        self._server_list = list[str]()

        self._dns_update_lock = asyncio.Lock()

    def _parse_srv_record(self, record: ReturnRecordT) -> SrvParsedResultT:
        """
        parse the srv record value to a tuple of (target, port)
        """
        _, _, port, server_host = record["value"].split(" ")
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

    def _generate_records(self) -> AddRecordListT:
        records = AddRecordListT()
        for address_name, address_info in self._addresses.items():
            if address_name == "*":
                sub_domain_base = f"{self._managed_sub_domain}"
            else:
                sub_domain_base = f"{address_name}.{self._managed_sub_domain}"
            records.append(
                AddRecordT(
                    sub_domain=f"*.{sub_domain_base}",
                    value=address_info["host"],
                    record_type=address_info["type"],
                    ttl=600,
                )
            )
            for server_name in self._server_list:
                records.append(
                    AddRecordT(
                        sub_domain=f"_minecraft._tcp.{server_name}.{sub_domain_base}",
                        value=f"0 5 {address_info['port']} {server_name}.{sub_domain_base}.{self._dns_client.get_domain()}.",
                        record_type="SRV",
                        ttl=600,
                    )
                )

        return records

    async def _get_relevent_records(self) -> RecordListT:
        records = await self._dns_client.list_records()
        relevent_records = RecordListT()
        for record in records:
            if record["record_type"] in ("A", "AAAA", "CNAME") and record[
                "sub_domain"
            ].endswith(f".{self._managed_sub_domain}"):
                relevent_records.append(record)
            elif (
                record["record_type"] == "SRV"
                and record["sub_domain"].startswith(f"_minecraft._tcp.")
                and record["sub_domain"].endswith(f".{self._managed_sub_domain}")
            ):
                relevent_records.append(record)
        return relevent_records

    async def _remove_relevent_records(self):
        records = await self._get_relevent_records()
        record_ids = [record["record_id"] for record in records]
        if record_ids:
            await self._dns_client.remove_records(record_ids)

    def set_dns_client(self, dns_client: DNSClient):
        """
        only sets the internal dns client, does not push or pull
        for test or migration purposes
        """
        self._dns_client = dns_client

    async def pull(self):
        """
        pull the address list from the dns record
        """
        record_list = await self._get_relevent_records()
        self._server_list.clear()
        self._addresses.clear()

        port_map = dict[str, int]()
        for record in record_list:
            if record["record_type"] == "SRV":
                parsed_result = self._parse_srv_record(record)
                if parsed_result["server_name"] not in self._server_list:
                    self._server_list.append(parsed_result["server_name"])
                port_map[parsed_result["address_name"]] = parsed_result["port"]
            else:
                address_name = record["sub_domain"].split(".")[-2]
                # record_type must be A or AAAA or CNAME
                # chill pylance
                self._addresses[address_name] = AddressInfoT(
                    type=record["record_type"],  # type: ignore
                    host=record["value"],
                    port=0,
                )

        for address_name, address_info in self._addresses.items():
            address_info["port"] = port_map[address_name]

    async def push(self):
        """
        sync the dns record to the address list
        """
        # we want to make sure only one push is running at the same time
        async with self._dns_update_lock:
            await self._remove_relevent_records()
            await self._dns_client.add_records(self._generate_records())

    async def set_addresses(self, addresses: AddressesT):
        """
        the caller should call push() after calling this function
            in order to sync the dns record
        """
        self._addresses = addresses

    async def get_addresses(self) -> AddressesT:
        """
        the caller should call pull() before calling this function
            in order to sync the dns record
        """
        return self._addresses

    async def set_server_list(self, server_list: list[str]):
        """
        the caller should call push() after calling this function
            in order to sync the dns record
        """
        self._server_list = server_list

    async def get_server_list(self) -> list[str]:
        """
        the caller should call pull() before calling this function
            in order to sync the dns record
        """
        return self._server_list
