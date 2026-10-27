# A trailing comment is not a statement: in a public method, a leg, an envelope leg and a module leg, each
# with and without a docstring.
# Readers moved to module level (R3); the envelope legs are plain forwards here.
TOOL_RESULT = decoder(ToolResult)


X = decoder(X)
Y = decoder(Y)
Z = decoder(Z)


async def _fetch_feed(client: AsyncBaseClient, path: str) -> bytes:
    return await client.get(path, expect=as_bytes)
    # the whole body


async def _fetch_doc(client: AsyncBaseClient, path: str) -> bytes:
    """One feed."""
    return await client.get(path, expect=as_bytes)
    # the whole body


class TrailingClient(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.get("x", expect=X)
        # nothing else

    async def get_y(self) -> Y:
        """One y."""
        return await self.get("y", expect=Y)
        # nothing else

    async def get_z(self, s: str) -> Z:
        return await self._leg(s)

    async def _leg(self, s: str) -> Z:
        return await self.get(t"z/{s}", expect=Z)
        # nothing else

    async def get_w(self, s: str) -> Z:
        return await self._doc_leg(s)

    async def _doc_leg(self, s: str) -> Z:
        """A leg."""
        return await self.get(t"w/{s}", expect=Z)
        # nothing else

    async def fetch_a(self) -> bytes:
        return await _fetch_feed(self, "a")

    async def fetch_b(self) -> bytes:
        return await _fetch_doc(self, "b")

    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        return await self.post(t"tools/{name}", body=_WRITE(arguments), expect=TOOL_RESULT)
        # nothing else

    async def _call_doc[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        """One tool."""
        return await self.post(t"tools/{name}", body=_WRITE(arguments), expect=TOOL_RESULT)
        # nothing else

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        return await self._call_tool("get_accounts", arguments, AccountsPayload)

    async def get_portfolio(self, arguments: NoArguments) -> PortfolioPayload:
        return await self._call_doc("get_portfolio", arguments, PortfolioPayload)
