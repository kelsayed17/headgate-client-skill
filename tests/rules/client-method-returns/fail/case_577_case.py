_DEC = decoder(Any)


class C(AsyncBaseClient):
    async def get_a(self) -> A:
        return await self.get("a", expect=_DEC)
