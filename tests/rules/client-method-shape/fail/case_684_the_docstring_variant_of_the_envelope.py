# The docstring variant of the envelope: a statement before it, a non-constructor envelope, a forward of a parameter.
class RobinhoodMCPClient(AsyncBaseClient):
    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        self._calls += 1
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        return await self.post("mcp/trading", body=_WRITE(request), expect=mcp_serde.decoder(request.id, name, payload))

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        return await self._call_tool("get_accounts", arguments, AccountsPayload)
