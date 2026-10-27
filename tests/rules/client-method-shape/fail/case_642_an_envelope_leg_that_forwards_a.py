# An envelope leg that forwards a parameter rather than its envelope; builds it with a function; reads a
# public attribute into it; forwards with a built keyword; runs on past its forward (with and without a
# docstring); passes the writer an extra argument.
class RobinhoodMCPClient(AsyncBaseClient):
    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        request = MCPToolCall(params=MCPToolCallParams(name=name, arguments=arguments))
        return await self.post("mcp/trading", body=_WRITE(arguments), expect=mcp_serde.decoder(request.id, name, payload))

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        return await self._call_tool("get_accounts", arguments, AccountsPayload)
