# An answer that is not a decoded reader: nothing, as_bytes, a lambda, a self attribute, an unknown or
# non-reader function.
class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=Expect(decoder(X)).on(404, nothing))
