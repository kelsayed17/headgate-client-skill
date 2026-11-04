# A `fetch_` name over a decoded model, its reader at module level.
QUOTE = decoder(Quote)


class C(AsyncBaseClient):
    async def fetch_quote(self) -> Quote:
        return await self.get("quote", expect=QUOTE)
