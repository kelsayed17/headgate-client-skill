# The same case with its readers moved to module level (R3).
ORDER = decoder(Order)


class C(AsyncBaseClient):
    async def cancel(self, order_id: str) -> None:
        return await self.delete(t"orders/{order_id}", expect=ORDER)
