# `fetch` alone is the prefix too.
class C(AsyncBaseClient):
    async def fetch(self) -> Quote:
        return await self.get("quote", expect=decoder(Quote))
