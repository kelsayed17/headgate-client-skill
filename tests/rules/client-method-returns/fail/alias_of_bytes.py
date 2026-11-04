# A module alias of `bytes` in the return: followed from the method.
Raw = bytes


class C(AsyncBaseClient):
    async def get_a(self) -> Raw:
        return await self.get("a", expect=decoder(bytes))
