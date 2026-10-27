class C(AsyncBaseClient):
    async def get_x(self) -> X | NotFound:
        return await self.get("x", expect=_OTHER.on(404, decoder(NotFound)))
