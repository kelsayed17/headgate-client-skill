# A void with no expect=nothing anywhere (through a delegate).
class C(AsyncBaseClient):
    async def cancel(self, order_id: str) -> None:
        return await self._leg(order_id)

    async def _leg(self, order_id: str) -> None:
        await self.delete(t"orders/{order_id}", expect=nothing)
