# Subclasses of an imported `_` base, an imported public client (bare and dotted), a local public client.
# The same case with its readers moved to module level (R3).
X = decoder(X)


class HostClient(AsyncBaseClient):
    """Any client module holds at least one of these."""


class C(_Imported):
    async def get_x(self) -> Any:
        return await self.get("x", expect=X)
