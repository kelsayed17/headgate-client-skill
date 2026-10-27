class C(AsyncBaseClient):
    async def _raw(self) -> httpx2.Response:
        return await self._http_client.get("x")
