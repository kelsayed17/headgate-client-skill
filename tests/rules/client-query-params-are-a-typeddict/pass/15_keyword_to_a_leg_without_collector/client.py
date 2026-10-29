class C(AsyncBaseClient):
    async def get_x(self, name: str) -> R:
        return await self._call_tool("x", name=name)

    async def _call_tool(self, tool: str, name: str) -> R:
        return await self.post("tools", body=_ENVELOPE(name), expect=decoder(R))
