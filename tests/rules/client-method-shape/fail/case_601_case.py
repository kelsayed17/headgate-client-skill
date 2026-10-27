# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, user_id: UUID) -> X:
        return await self.get("x", headers=self._uid(str(user_id)), expect=X)
