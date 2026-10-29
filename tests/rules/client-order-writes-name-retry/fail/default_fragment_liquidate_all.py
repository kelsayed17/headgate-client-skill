class Broker(AsyncBaseClient):
    async def liquidate_all(self) -> list[Order]:
        return await self.post("liquidate", expect=ORDERS)
