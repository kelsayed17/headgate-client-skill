# expect=nothing through an alias, and as_bytes through an alias.
_NOTHING = nothing

class C(AsyncBaseClient):
    async def cancel(self, order_id: str) -> Order:
        return await self.delete(t"orders/{order_id}", expect=_NOTHING)
