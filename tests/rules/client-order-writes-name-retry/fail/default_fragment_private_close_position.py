class Broker(AsyncBaseClient):
    async def _close_position_by_id(self, position_id: str) -> Order:
        return await self.delete(t"positions/{position_id}", expect=ORDER)
