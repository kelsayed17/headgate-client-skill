class C(AsyncBaseClient):
    async def cancel(self, order_id: str) -> None:
        await self.delete(t"orders/{order_id}", expect=Expect(nothing).on(404, decoder(NotFound)))
