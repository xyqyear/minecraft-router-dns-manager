import asyncio
from typing import Callable, TypedDict

import aiohttp

from ..config import config
from ..dns.mcdns import AddressesT, AddressInfoT
from ..logger import logger


class MappingValueT(TypedDict):
    ip: str
    port: int


class NatmapMonitorClient:
    def __init__(self, base_url: str, timeout: int = 5) -> None:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        )

        self._timeout = timeout

        self._url = base_url
        if not self._url.endswith("/"):
            self._url += "/"

    async def listen_to_ws(self, on_message: Callable[..., None]):
        """
        should be called in conjunction with asyncio.create_task,
        since it's a infinite loop
        """
        while True:
            try:
                logger.info("connecting to natmap monitor ws...")
                async with self._session.ws_connect(
                    self._url + "ws", timeout=self._timeout
                ) as ws:  # type: ignore
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:  # type: ignore
                            message: dict[str, MappingValueT] = msg.json()
                            for port in self._get_port_to_address_name_mapping_from_config().keys():
                                if f"tcp:{port}" in message:
                                    logger.info(
                                        f"received relevent natmap message: {message}"
                                    )
                                    on_message()

            except Exception as e:
                logger.warning(f"error while connecting natmap monitor with ws: {e}")
            logger.info("connection to natmap monitor ws closed")
            await asyncio.sleep(self._timeout)

    def _get_port_to_address_name_mapping_from_config(self) -> dict[int, str]:
        return {
            address.params.internal_port: address_name
            for address_name, address in config.addresses.items()
            if address.type == "natmap"
        }

    async def _get_mappings(self) -> dict[str, MappingValueT]:
        async with self._session.get(self._url + "all_mappings") as response:
            return await response.json()

    async def get_addresses_filtered_by_config(self) -> AddressesT:
        mappings = await self._get_mappings()
        port_to_address_name = self._get_port_to_address_name_mapping_from_config()

        addresses = AddressesT()
        for port, address_name in port_to_address_name.items():
            protocol_and_port = f"tcp:{port}"
            if protocol_and_port not in mappings:
                logger.warning(f"port {port} not found in natmap mappings")
                continue

            mapping = mappings[protocol_and_port]
            addresses[address_name] = AddressInfoT(
                type="A",
                host=mapping["ip"],
                port=mapping["port"],
            )

        return addresses
