# An await as the ONLY fault (in a plain keyword); a lambda with no constructor in it.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get(await _path(), expect=X)
