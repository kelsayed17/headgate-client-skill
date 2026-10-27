# The keyword spelling of the root, as the clients README documents it.
# The same case with its readers moved to module level (R3).
OK_X_404_NOT_FOUND = Expect(ok=decoder(X)).on(404, decoder(NotFound))
OK_AS_BYTES_404_NOT_FOUND = Expect(ok=as_bytes).on(404, decoder(NotFound))


class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=OK_X_404_NOT_FOUND)

    async def fetch_y(self) -> bytes | NotFound:
        return await self.get("y", expect=OK_AS_BYTES_404_NOT_FOUND)
