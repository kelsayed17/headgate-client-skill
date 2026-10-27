# The source's fetch_/get_ naming clause (and its bytes/str alias clause) does not port: this passes here.
# The same case with its readers moved to module level (R3).
QUOTE = decoder(Quote)


class C(AsyncBaseClient):
    async def fetch_quote(self) -> Quote:
        return await self.get("quote", expect=QUOTE)
