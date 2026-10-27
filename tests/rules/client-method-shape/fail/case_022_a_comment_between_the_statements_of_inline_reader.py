# A comment BETWEEN the statements of each kind of leg is not a statement either.
# R3: the source's inline reader; `expect=` is a module-level name here.
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
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        # the envelope, forwarded
        return await self.post("mcp/trading", body=_WRITE(request), expect=mcp_serde.decoder(request.id, name, payload))

    async def _call_doc[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        """One tool."""
        # the envelope
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        # forwarded
        return await self.post("mcp/trading", body=_WRITE(request), expect=mcp_serde.decoder(request.id, name, payload))

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        return await self._call_tool("get_accounts", arguments, AccountsPayload)

    async def get_portfolio(self, arguments: NoArguments) -> PortfolioPayload:
        return await self._call_doc("get_portfolio", arguments, PortfolioPayload)
