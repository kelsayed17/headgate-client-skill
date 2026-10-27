# An alias as a dotted name, a subscript assignment and a None union.
Payload = typing.Any


class C(AsyncBaseClient):
    async def get_a(self) -> Payload:
        return await self.get("a", expect=decoder(A))
