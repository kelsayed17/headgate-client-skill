# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def post_a(self, body=_BODY) -> A:
        return await self.post("/a", json=body, expect=A)
