# `nothing` does not arrive through an alias: a void declares `expect=nothing` itself.
NOTHING = nothing


class C(AsyncBaseClient):
    async def cancel_order(self, order_id: str) -> None:
        await self.delete(t"orders/{order_id}", expect=NOTHING)
