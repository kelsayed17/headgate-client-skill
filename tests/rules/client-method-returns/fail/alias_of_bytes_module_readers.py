# A module alias of `bytes`, its reader at module level.
BYTES = decoder(bytes)


Raw = bytes


class C(AsyncBaseClient):
    async def get_a(self) -> Raw:
        return await self.get("a", expect=BYTES)
