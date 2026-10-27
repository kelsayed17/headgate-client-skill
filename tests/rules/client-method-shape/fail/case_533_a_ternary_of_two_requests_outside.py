# A ternary of two requests, outside and inside the await.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, live: bool) -> X:
        return await self.get("live", expect=X) if live else await self.get("paper", expect=X)
