async def _fetch(client: AsyncBaseClient, path: str) -> bytes:
    return await client.get(path, expect=as_bytes)


class C(AsyncBaseClient):
    async def fetch_x(self) -> bytes:
        return await _fetch(self, "x")
