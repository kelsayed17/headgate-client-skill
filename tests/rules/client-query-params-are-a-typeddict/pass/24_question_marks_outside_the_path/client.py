_HINT = t"is {name} listed?"


class C(AsyncBaseClient):
    async def _call_tool(self, name: str) -> R:
        request = ToolCall("lookup?", params=ToolCallParams(name=name))
        return await self.post("tools", body=_ENVELOPE(request), expect=decoder(R))
