# `params=params` where `params` is not the method's own parameter: a module global.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", params=params, expect=X)
