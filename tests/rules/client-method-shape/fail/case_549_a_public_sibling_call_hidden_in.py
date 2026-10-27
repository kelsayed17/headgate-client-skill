# A public sibling call hidden in the path, and an uncalled public reference.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, s: str) -> X:
        return await self.get(t"x/{await self.get_id(s)}", expect=X)
