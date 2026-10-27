# R10: an UPPER_CASE name the module does not bind is not a module-level policy.
ORDER = decoder(Order)


class C(AsyncBaseClient):
    async def place_order(self, order: NewOrder) -> Order:
        return await self.post("orders", body=NEW_ORDER(order), expect=ORDER, retry=ORDER_RETRY)
