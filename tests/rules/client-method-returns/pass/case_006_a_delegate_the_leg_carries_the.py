# A delegate: the leg carries the expect, the public method its payload type.
class RobinhoodMCPClient(AsyncBaseClient):
    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T], *, retry: bool = True) -> T:
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        return await self.post("mcp/trading", json=to_builtins(request), expect=mcp_serde.decoder(request.id, name, payload), retry=retry)

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        return await self._call_tool("get_accounts", arguments, AccountsPayload)
