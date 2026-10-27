class OrdersClient(AsyncBaseClient):
    async def cancel_order(self, order_id: str) -> CancelResponse:
        return await self.post(t"api/v1/crypto/trading/orders/{quote(order_id, safe='')}/cancel/", expect=decoder(CancelResponse))
