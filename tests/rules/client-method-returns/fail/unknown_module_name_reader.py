# An UPPER_CASE name bound to something that is not a reader (a string) is not a house reader.
ORDERS_PATH = "orders"


class C(AsyncBaseClient):
    async def get_orders(self) -> OrderPage:
        return await self.get("orders", expect=ORDERS_PATH)
