_ROWS = decoder(list[Row])
_NOTHING = nothing

class C(AsyncBaseClient):
    async def cancel(self, order_id: str) -> Order:
        return await self.delete(t"orders/{order_id}", expect=_NOTHING)
