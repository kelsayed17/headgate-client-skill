# R10: a retry policy built at the call is built per call; declare it once at module level.
ORDER = decoder(Order)


class C(AsyncBaseClient):
    async def place_order(self, order: NewOrder) -> Order:
        return await self.post("orders", body=NEW_ORDER(order), expect=ORDER, retry=RetryPolicy(attempts=1))
