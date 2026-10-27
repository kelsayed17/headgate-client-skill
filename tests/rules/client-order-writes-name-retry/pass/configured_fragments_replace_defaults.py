# headgate-verify-config: {"write_name_fragments": ["redeem"]}
# A configured list replaces the defaults: `place_order` is not a fragment here.
class Shop(AsyncBaseClient):
    async def place_order(self, order: NewOrder) -> Order:
        return await self.post("orders", body=NEW_ORDER(order), expect=ORDER)
