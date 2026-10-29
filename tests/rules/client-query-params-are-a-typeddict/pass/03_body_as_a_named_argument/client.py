class C(AsyncBaseClient):
    async def place_order(self, account_id: str, body: OrderBody) -> Order:
        return await self.post(t"accounts/{account_id}/orders", body=_ORDER_BODY(body), expect=decoder(Order))
