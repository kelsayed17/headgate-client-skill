# The envelope sent under a keyword that is not body=.
class RobinhoodMCPClient(AsyncBaseClient):
    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        return await self.post("mcp/trading", expect=_WRITE(request))

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        return await self._call_tool("get_accounts", arguments, AccountsPayload)
