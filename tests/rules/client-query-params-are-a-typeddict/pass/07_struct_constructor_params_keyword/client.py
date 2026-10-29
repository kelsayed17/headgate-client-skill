class C(AsyncBaseClient):
    async def _call_tool(self, name: str, arguments: Args) -> R:
        request = ToolCall(params=ToolCallParams(name=name, arguments=arguments))
        return await self.post("tools", body=_ENVELOPE(request), expect=decoder(R))
