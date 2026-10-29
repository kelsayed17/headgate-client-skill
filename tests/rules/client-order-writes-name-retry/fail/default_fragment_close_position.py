class Broker(AsyncBaseClient):
    async def close_position(self, symbol: str) -> Order:
        return await self.delete(t"positions/{symbol}", expect=ORDER)
