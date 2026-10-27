# A cancel-and-replace submits a new order: `replace` makes a cancel_ name executing.
class Shop(AsyncBaseClient):
    async def cancel_and_replace_order(self, order_id: str, order: NewOrder) -> Order:
        return await self.post(t"orders/{order_id}/replace", body=NEW_ORDER(order), expect=ORDER)
