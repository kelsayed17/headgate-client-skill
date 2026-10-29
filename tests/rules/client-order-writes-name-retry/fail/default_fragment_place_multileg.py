class Broker(AsyncBaseClient):
    async def place_multileg(self, body: MultiLeg) -> Order:
        return await self.post("orders", body=MULTI_LEG(body), expect=ORDER)
