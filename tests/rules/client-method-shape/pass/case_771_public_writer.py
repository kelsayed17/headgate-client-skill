# A public UPPER_CASE writer applied to a request parameter: headgate's own `body=NEW_ORDER(order)` (the source
# required a `_` prefix; the spec and headgate's examples write the writer public).
X = decoder(X)


class C(AsyncBaseClient):
    async def add(self, body: Body) -> X:
        return await self.post("x", body=WRITE(body), expect=X)
