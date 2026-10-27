# A parameter of an ENCLOSING function is not the method's own.
# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, body: B) -> A:
        async def _inner(x: X) -> A:
            return await self.post("/a", json=body, expect=A)

        return await _inner(body)
