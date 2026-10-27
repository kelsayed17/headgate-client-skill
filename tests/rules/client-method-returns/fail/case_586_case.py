def _gone(resp: httpx2.Response, /) -> Gone:
    return Gone()


class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=Expect(decoder(X)).on(404, _missing))
