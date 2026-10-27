# I6: an alias hiding a forbidden type (or bytes/str from the fetch_ check), in a client module.
Payload = Any


class C(AsyncBaseClient):
    async def get_a(self) -> Payload:
        return await self.get("a", expect=decoder(A))
