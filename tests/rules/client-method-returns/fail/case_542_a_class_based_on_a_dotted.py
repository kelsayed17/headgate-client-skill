# A class based on a dotted AsyncBaseClient; a decorated one (the module's only client class).
class C(headgate.AsyncBaseClient):
    async def get_x(self) -> Any:
        return await self.get("x", expect=decoder(X))
