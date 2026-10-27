def _not_found(status: int) -> NotFound:
    return NotFound()


class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=Expect(decoder(X)).on(404, _not_found))
