# A trailing comment is not a statement: in a public method, a leg, an envelope leg and a module leg, each
# with and without a docstring.
# R3: the source's inline reader; `expect=` is a module-level name here.
async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    return await client.get(path, expect=as_bytes)
    # the whole body


async def _fetch_doc(client: AsyncBaseClient, path: str) -> bytes:
    """One feed."""
    return await client.get(path, expect=as_bytes)
    # the whole body


class TrailingClient(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=decoder(X))
        # nothing else

    async def get_y(self) -> Y:
        """One y."""
        return await self.get("y", expect=decoder(Y))
        # nothing else

    async def get_z(self, s: str) -> Z:
        return await self._leg(s)

    async def _leg(self, s: str) -> Z:
        return await self.get(t"z/{s}", expect=decoder(Z))
        # nothing else

    async def get_w(self, s: str) -> Z:
        return await self._doc_leg(s)

    async def _doc_leg(self, s: str) -> Z:
        """A leg."""
        return await self.get(t"w/{s}", expect=decoder(Z))
        # nothing else

    async def fetch_a(self) -> bytes:
        return await _fetch_feed(self, "a")

    async def fetch_b(self) -> bytes:
        return await _fetch_doc(self, "b")

    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        return await self.post("mcp/trading", body=_WRITE(request), expect=mcp_serde.decoder(request.id, name, payload))
        # nothing else

    async def _call_doc[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        """One tool."""
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        return await self.post("mcp/trading", body=_WRITE(request), expect=mcp_serde.decoder(request.id, name, payload))
        # nothing else

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        return await self._call_tool("get_accounts", arguments, AccountsPayload)

    async def get_portfolio(self, arguments: NoArguments) -> PortfolioPayload:
        return await self._call_doc("get_portfolio", arguments, PortfolioPayload)
