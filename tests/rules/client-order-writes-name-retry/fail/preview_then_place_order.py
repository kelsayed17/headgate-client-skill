# `preview` inside a name does not make it a preview: only a name starting with preview_.
class Shop(AsyncBaseClient):
    async def place_order_after_preview(self, order: NewOrder) -> Order:
        return await self.post("orders", body=NEW_ORDER(order), expect=ORDER)
