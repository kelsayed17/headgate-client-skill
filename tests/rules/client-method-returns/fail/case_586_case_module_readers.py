# The same case with its readers moved to module level (R3).
X_404_MISSING = Expect(decoder(X)).on(404, _missing)


def _gone(resp: httpx2.Response, /) -> Gone:
    return Gone()


class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=X_404_MISSING)
