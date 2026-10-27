class OrdersClient(AsyncBaseClient):
    async def cancel_order(self, order_id: str) -> CancelResponse:
        return await self.post(t"api/v1/crypto/trading/orders/{order_id}/cancel/", expect=decoder(CancelResponse))

    async def get_bars(self, symbol: str, year: int) -> Bars:
        return await self.get(t"v2/{symbol.lower()}/{year:04d}", expect=decoder(Bars))
