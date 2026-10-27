# A docstring-looking f-string is a statement, not a docstring.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, s: str) -> X:
        f"{s}"
        return await self.get("x", expect=X)
