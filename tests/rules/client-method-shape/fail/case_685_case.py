class RobinhoodMCPClient(AsyncBaseClient):
    async def _call_tool[T](self, name: str, arguments: Args, payload: type[T]) -> T:
        """One tool."""
        request = build_envelope(name, arguments)
        return await self.post("mcp/trading", body=_WRITE(request), expect=mcp_serde.decoder(request.id, name, payload))

    async def get_accounts(self, arguments: NoArguments) -> AccountsPayload:
        return await self._call_tool("get_accounts", arguments, AccountsPayload)
