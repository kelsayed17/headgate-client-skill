class Broker(AsyncBaseClient):
    async def close_option_position(self, body: Close) -> Order:
        return await self.post("options/close", body=CLOSE(body), expect=ORDER)
