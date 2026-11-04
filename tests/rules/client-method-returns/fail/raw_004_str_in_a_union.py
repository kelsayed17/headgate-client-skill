# `str` as one arm of a decoded union.
class C(AsyncBaseClient):
    async def get_quote(self) -> Quote | str:
        return await self.get("quote", expect=decoder(Quote | str))
