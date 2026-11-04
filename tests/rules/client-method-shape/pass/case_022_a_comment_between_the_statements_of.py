# A comment BETWEEN the statements of each kind of leg is not a statement either.
# Readers moved to module level (R3); the envelope legs are plain forwards here.


Z = decoder(Z)


async def _fetch_doc(client: AsyncBaseClient, path: str) -> bytes:
    """One feed."""
    # the one request
    return await client.get(path, expect=as_bytes)


class InteriorClient(AsyncBaseClient):
    async def get_w(self, s: str) -> Z:
        return await self._doc_leg(s)

    async def _doc_leg(self, s: str) -> Z:
        """A leg."""
        # the one request
        return await self.get(t"w/{s}", expect=decoder(Z))

    async def fetch_b(self) -> bytes:
        return await _fetch_doc(self, "b")

    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        # the envelope, forwarded
        return await self.post(t"tools/{name}", body=_WRITE(arguments), expect=decoder(ToolResult))

    async def _call_doc[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        """One tool."""
        # the envelope
        # forwarded
        return await self.post(t"tools/{name}", body=_WRITE(arguments), expect=decoder(ToolResult))

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        return await self._call_tool("get_accounts", arguments, AccountsPayload)

    async def get_portfolio(self, arguments: NoArguments) -> PortfolioPayload:
        return await self._call_doc("get_portfolio", arguments, PortfolioPayload)
