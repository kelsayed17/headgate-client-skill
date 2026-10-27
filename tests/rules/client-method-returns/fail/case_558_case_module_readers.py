# The same case with its readers moved to module level (R3).
ORDER_404_NOT_FOUND = Expect(decoder(Order)).on(404, decoder(NotFound))


class C(AsyncBaseClient):
    async def cancel(self, order_id: str) -> None:
        await self.delete(t"orders/{order_id}", expect=ORDER_404_NOT_FOUND)
