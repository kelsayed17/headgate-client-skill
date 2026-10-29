async def _fetch(client: AsyncBaseClient, path: str, **params: Unpack[XParams]) -> bytes:
    return await client.get(path, params=params, expect=as_bytes)


class C(AsyncBaseClient):
    async def fetch_x(self, symbol: str) -> bytes:
        return await _fetch(self, "x", symbol=symbol)
