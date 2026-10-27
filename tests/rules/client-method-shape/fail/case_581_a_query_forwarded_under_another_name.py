# A query forwarded under another name.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, query: Q) -> X:
        return await self.get("x", params=query, expect=X)
