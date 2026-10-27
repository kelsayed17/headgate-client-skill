# An alias as a dotted name, a subscript assignment and a None union.
# The same case with its readers moved to module level (R3).
A = decoder(A)


Payload = typing.Any


class C(AsyncBaseClient):
    async def get_a(self) -> Payload:
        return await self.get("a", expect=A)
