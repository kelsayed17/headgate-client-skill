# Minor: only the request keywords, and the transport knobs as a literal or a parameter.
# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def get_a(self, key: str) -> A:
        return await self.get("/a", auth=_bearer(key), expect=A)
