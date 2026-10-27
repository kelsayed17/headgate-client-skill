# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, name: str) -> X:
        return await self.post("x", data=self._form(name), expect=X)
