# No annotation, and a quoted one.
# The same case with its readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self):
        return await self.get("x", expect=X)
