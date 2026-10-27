# The same case with its readers moved to module level (R3).
X = decoder(X)


class HostClient(AsyncBaseClient):
    """Any client module holds at least one of these."""


class Sub(public.PublicClient):
    async def get_x(self) -> Any:
        return await self.get("x", expect=X)
