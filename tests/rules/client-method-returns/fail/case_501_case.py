class C(AsyncBaseClient):
    async def cancel(self, order_id: str) -> None:
        await self.delete(t"orders/{order_id}", expect=as_bytes)
