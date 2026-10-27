# I6: what a decoder decodes into is the return type too, at a public method and anywhere in a client module.
# The same case with its readers moved to module level (R3).
ANY = decoder(Any)


class C(AsyncBaseClient):
    async def get_a(self) -> A:
        return await self.get("a", expect=ANY)
