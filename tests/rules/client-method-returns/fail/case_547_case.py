class Public(AsyncBaseClient):
    """A public client."""


class Sub(Public):
    async def get_x(self) -> Any:
        return await self.get("x", expect=decoder(X))
