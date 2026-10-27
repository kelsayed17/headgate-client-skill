# The written form: a module constant, read from the class.
_ORDERS_PATH = "v1/accounts/{account_id}/orders"

class TradierClient(AsyncBaseClient):
    async def get_orders(self) -> bytes:
        return await self.get(_ORDERS_PATH)
