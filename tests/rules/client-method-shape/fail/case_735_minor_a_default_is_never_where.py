# Minor: a default is never where a request is built: a call, a dict, a lambda; and a FORWARDED parameter
# defaults to None or not at all.
# Readers moved to module level (R3).
A = decoder(A)


class C(AsyncBaseClient):
    async def post_b(self, body: B, extra: B = B(kind="market", tif="day")) -> A:
        return await self.post("/b", body=_WRITE(body), expect=A)
