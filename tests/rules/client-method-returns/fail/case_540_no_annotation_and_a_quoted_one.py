# No annotation, and a quoted one.
class C(AsyncBaseClient):
    async def get_x(self):
        return await self.get("x", expect=decoder(X))
