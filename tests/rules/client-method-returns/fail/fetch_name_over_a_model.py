# A `fetch_` name over a decoded model: the prefix named a raw read, which is gone, so a read is `get_`.
class C(AsyncBaseClient):
    async def fetch_quote(self) -> Quote:
        return await self.get("quote", expect=decoder(Quote))
