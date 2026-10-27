# I6: what a decoder decodes into is the return type too, at a public method and anywhere in a client module.
class C(AsyncBaseClient):
    async def get_a(self) -> A:
        return await self.get("a", expect=decoder(Any))
