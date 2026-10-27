# A void that also reads a body, and an alias of nothing beside a real decoder alias.
# The same case with its readers moved to module level (R3).
AUDIT = decoder(Audit)


class C(AsyncBaseClient):
    async def cancel(self, order_id: str) -> None:
        await self.delete(t"orders/{order_id}", expect=nothing)
        await self.post("audit", expect=AUDIT)
