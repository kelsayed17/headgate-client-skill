# A reader function whose Response is not its FIRST parameter.
# The same case with its readers moved to module level (R3).
X_404_NOT_FOUND = Expect(decoder(X)).on(404, _not_found)


def _not_found(status: int, resp: httpx2.Response, /) -> NotFound:
    return NotFound()


class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=X_404_NOT_FOUND)
