# A leg without a docstring that runs on past its forward; a leg with a docstring whose statement is not a forward.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, s: str) -> X:
        return await self._leg(s)

    async def _leg(self, s: str) -> X:
        return await self.get(t"x/{s}", expect=X)
        self._calls += 1
