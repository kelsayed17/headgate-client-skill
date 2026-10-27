# headgate's own example shape: `place_order` posts with no retry= under the default fragments.
class Shop(AsyncBaseClient):
    async def place_order(self, order: NewOrder) -> Order | Rejection:
        return await self.post("orders", body=NEW_ORDER(order), expect=ORDER_OR_REJECTION)
