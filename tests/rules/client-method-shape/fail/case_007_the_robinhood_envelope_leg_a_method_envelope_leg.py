# The JSON-RPC envelope leg (one provider's shape) is dropped: a leg is a plain forward, so this fails.
# The Robinhood envelope leg: a method per tool delegating to ONE private leg that builds the
# JSON-RPC envelope and forwards it.
class RobinhoodMCPClient(AsyncBaseClient):
    async def _call_tool[T](
        self, name: str, arguments: Mapping[str, object], payload: type[T], *, retry: bool = True
    ) -> T:
        """``POST mcp/trading`` — invoke one tool and return its decoded payload."""
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        return await self.post(
            "mcp/trading",
            body=_WRITE(request),
            expect=mcp_serde.decoder(request.id, name, payload),
            retry=retry,
        )

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        """``get_accounts`` — every account the grant reaches."""
        return await self._call_tool("get_accounts", arguments, AccountsPayload)

    async def place_equity_order(self, arguments: PlaceEquityOrderArguments) -> PlaceEquityOrderPayload:
        return await self._call_tool("place_equity_order", arguments, PlaceEquityOrderPayload, retry=False)
