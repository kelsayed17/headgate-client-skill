# An attribute base, a second base, a metaclass, a class decorator.
# Readers moved to module level (R3).
X = decoder(X)


class C(headgate.AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=X)
