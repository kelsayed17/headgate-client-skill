class C(AsyncBaseClient):
    async def cancel(self, order_id: str) -> Optional[None]:
        await self.delete(t"orders/{order_id}", expect=nothing)
