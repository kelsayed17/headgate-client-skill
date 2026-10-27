# An attribute constructor in a plain keyword; an await in the path.
class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=headgate.Reader(X))
