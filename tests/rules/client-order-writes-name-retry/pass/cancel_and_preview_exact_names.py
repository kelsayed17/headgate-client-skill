# headgate-verify-config: {"write_name_fragments": ["cancel", "preview", "order"]}
# A name that is exactly `cancel` or `preview` is not executing either.
class Shop(AsyncBaseClient):
    async def cancel(self, order_id: str) -> None:
        await self.delete(t"orders/{order_id}", expect=nothing)

    async def preview(self, order: NewOrder) -> Preview:
        return await self.post("orders/preview", body=NEW_ORDER(order), expect=PREVIEW)
