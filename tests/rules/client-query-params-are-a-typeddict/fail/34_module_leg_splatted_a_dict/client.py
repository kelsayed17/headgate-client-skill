class C(AsyncBaseClient):
    async def fetch_x(self, symbol: str) -> bytes:
        return await _fetch(self, "x", **{"symbol": symbol})
