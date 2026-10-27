# A header built by a module function, even from parameters.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, user_id: UUID) -> X:
        return await self.get("x", headers=build_headers(user_id), expect=X)
