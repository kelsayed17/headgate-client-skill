# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def get_x(self, cookies: Cookies) -> X:
        return await self.get("x", cookies=cookies, expect=X)
