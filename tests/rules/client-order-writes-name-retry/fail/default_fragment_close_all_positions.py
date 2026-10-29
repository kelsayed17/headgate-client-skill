class Broker(AsyncBaseClient):
    async def close_all_positions(self) -> list[Order]:
        return await self.delete("positions", expect=ORDERS)
