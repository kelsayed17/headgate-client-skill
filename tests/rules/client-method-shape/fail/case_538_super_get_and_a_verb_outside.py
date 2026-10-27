# super().get and a verb outside get|post|put|patch|delete|head.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await super().get("x", expect=X)
