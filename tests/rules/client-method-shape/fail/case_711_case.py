class C(AsyncBaseClient):
    async def place_order(self, account: str, symbol: str, qty: int, side: str) -> Ack:
        return await self._place(account, symbol, qty, side, Ack)

    async def _place(self, account: str, symbol: str, qty: int, side: str, t: type) -> Ack:
        order = OrderBody(symbol=symbol, qty=qty, side=side, type="market", tif="day", extended_hours=True)
        return await self.post(t"/accounts/{account}/orders", body=_WRITE(order), retry=False, expect=decoder(t))
