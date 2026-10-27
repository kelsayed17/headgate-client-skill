# An envelope leg that forwards something other than the envelope it built.
class RobinhoodMCPClient(AsyncBaseClient):
    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        return await self.post("mcp/trading", json={"id": 1, "req": request}, expect=mcp_serde.decoder(request.id, name, payload))

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        return await self._call_tool("get_accounts", arguments, AccountsPayload)
