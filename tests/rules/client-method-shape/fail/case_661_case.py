# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, token: str) -> X:
        return await self.post("x", idempotency_key=self._key(token), expect=X)
