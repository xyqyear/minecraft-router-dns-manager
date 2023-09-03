import asyncio
import json as jsonlib
from typing import Awaitable, Literal, NotRequired, Optional, TypedDict, cast

import aiohttp


class RoutePoseDataT(TypedDict):
    serverAddress: str
    backend: str


HeadersT = TypedDict(
    "HeadersT", {"Accept": NotRequired[str], "Content-Type": NotRequired[str]}
)


RoutesT = dict[str, str]


class MCRouter:
    def __init__(self, base_url: str) -> None:
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))

        self._base_url = base_url

        if not self._base_url.endswith("/"):
            self._base_url += "/"

    async def _send_request(
        self,
        method: Literal["GET", "POST", "DELETE"],
        path: str,
        headers: Optional[HeadersT] = None,
        json: Optional[RoutePoseDataT] = None,
    ) -> Optional[RoutesT]:
        async with self._session.request(
            method, self._base_url + path, headers=headers, json=json
        ) as response:
            response_str = await response.text()

        if response_str:
            return jsonlib.loads(response_str)

    async def get_all_routes(self) -> RoutesT:
        response = await self._send_request(
            "GET", "routes", headers={"Accept": "application/json"}
        )
        return cast(RoutesT, response)

    async def _remove_route(self, route: str):
        await self._send_request("DELETE", f"routes/{route}")

    async def _remove_all_routes(self):
        all_routes = await self.get_all_routes()
        tasks = list[Awaitable[None]]()
        for route in all_routes.keys():
            tasks.append(self._remove_route(route))

        await asyncio.gather(*tasks)

    async def _add_route(self, route: str, backend: str):
        await self._send_request(
            "POST",
            "routes",
            headers={"Content-Type": "application/json"},
            json=RoutePoseDataT(serverAddress=route, backend=backend),
        )

    async def _add_routes(self, routes: RoutesT):
        tasks = list[Awaitable[None]]()
        for route, backend in routes.items():
            tasks.append(self._add_route(route, backend))

        await asyncio.gather(*tasks)

    async def override_routes(self, routes: RoutesT):
        await self._remove_all_routes()
        await self._add_routes(routes)
