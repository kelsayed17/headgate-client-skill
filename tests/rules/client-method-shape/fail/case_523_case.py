class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=as_bytes, deadline=LONG if FAST else SHORT)
