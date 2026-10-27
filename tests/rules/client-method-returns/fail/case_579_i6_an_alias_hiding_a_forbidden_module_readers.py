# I6: an alias hiding a forbidden type (or bytes/str from the fetch_ check), in a client module.
# The same case with its readers moved to module level (R3).
A = decoder(A)


Payload = Any


class C(AsyncBaseClient):
    async def get_a(self) -> Payload:
        return await self.get("a", expect=A)
