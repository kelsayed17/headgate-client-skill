async def get_bars(self, symbol: str) -> bytes:
    return await self.get(t"/v2/stocks/{symbol}/bars", expect=as_bytes)
