# A constructor call as any keyword value, and a dict literal anywhere in the call.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=X, timeout=httpx.Timeout(5.0))
