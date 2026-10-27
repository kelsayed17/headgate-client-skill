# The keyword spelling of the Expect root is one argument too.
# Readers moved to module level (R3).
OK_X_404_NOT_FOUND = Expect(ok=decoder(X)).on(404, decoder(NotFound))


class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=OK_X_404_NOT_FOUND)
