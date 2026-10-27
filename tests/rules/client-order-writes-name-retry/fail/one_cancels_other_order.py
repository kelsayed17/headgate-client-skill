# An OCO placement holds `cancel` but places orders: only a name STARTING with cancel_ is a cancel.
class Shop(AsyncBaseClient):
    async def place_one_cancels_other_order(self, order: OcoOrder) -> Order:
        return await self.post("orders/oco", body=OCO(order), expect=ORDER)
