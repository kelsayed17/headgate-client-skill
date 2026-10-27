# An answer that is not a decoded reader: nothing, as_bytes, a lambda, a self attribute, an unknown or
# non-reader function.
# The same case with its readers moved to module level (R3).
X_404_NOTHING = Expect(decoder(X)).on(404, nothing)


class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=X_404_NOTHING)
