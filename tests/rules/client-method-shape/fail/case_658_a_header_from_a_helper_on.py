# A header from a helper on another object; each body keyword built by a call.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, user_id: UUID) -> X:
        return await self.get("x", headers=_HEADERS.for_user(user_id), expect=X)
