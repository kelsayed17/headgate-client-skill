class HostClient(AsyncBaseClient):
    """Any client module holds at least one of these."""


class Sub(PublicClient):
    async def get_x(self) -> Any:
        return await self.get("x", expect=decoder(X))
