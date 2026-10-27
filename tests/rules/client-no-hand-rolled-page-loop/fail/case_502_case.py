class CoinbaseClient(AsyncBaseClient):
    async def get_all(self) -> list[Fill]:
        while True:
            page = await self.get("/fills")
            if not page.cursor:
                return page.fills
