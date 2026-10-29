class C(AsyncBaseClient):
    async def get_x(self, symbol: str, **params: Unpack[XParams]) -> X:
        return await self._leg(t"x/{symbol}", **params)

    async def get_y(self, name: str) -> R:
        return await self._call_tool("y", name=name)

    async def _leg(self, path: Template, **params: Unpack[XParams]) -> X:
        return await self.get(path, params=params, expect=decoder(X))

    async def _call_tool(self, tool: str, name: str) -> R:
        return await self.post("tools", body=_ENVELOPE(name), expect=decoder(R))
