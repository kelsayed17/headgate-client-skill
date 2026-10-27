# A reader that is public, or unknown beside one that exists.
def not_found(resp: httpx2.Response, /) -> NotFound:
    return NotFound()


class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=Expect(decoder(X)).on(404, not_found))
