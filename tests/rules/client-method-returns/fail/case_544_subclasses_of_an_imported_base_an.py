# Subclasses of an imported `_` base, an imported public client (bare and dotted), a local public client.
class HostClient(AsyncBaseClient):
    """Any client module holds at least one of these."""


class C(_Imported):
    async def get_x(self) -> Any:
        return await self.get("x", expect=decoder(X))
