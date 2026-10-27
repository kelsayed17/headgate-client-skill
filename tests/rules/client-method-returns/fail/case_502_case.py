class C(AsyncBaseClient):
    async def cancel(self, order_id: str) -> None:
        return await self.delete(t"orders/{order_id}", expect=decoder(Order))
