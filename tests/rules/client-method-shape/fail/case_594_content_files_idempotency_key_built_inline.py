# content= / files= / idempotency_key= built inline; cookies=, which no headgate verb takes.
# Readers moved to module level (R3).
X = decoder(X)


class C(AsyncBaseClient):
    async def upload(self, parts: list[bytes]) -> X:
        return await self.post("x", content=b"".join(parts), expect=X)
