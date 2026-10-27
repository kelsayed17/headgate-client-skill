# A cancel (re-sending one is the case you want to land) and a preview are not executing writes, whatever fragment
# their name holds.
class Shop(AsyncBaseClient):
    async def cancel_order(self, order_id: str) -> None:
        await self.delete(t"orders/{order_id}", expect=nothing)

    async def preview_order(self, order: NewOrder) -> Preview:
        return await self.post("orders/preview", body=NEW_ORDER(order), expect=PREVIEW)
