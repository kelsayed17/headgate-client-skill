class C(AsyncBaseClient):
    _H = {"X-Api-\x4bey": "k"}

    async def get_x(self) -> X:
        return await self.get("/v1/\x78", expect=decoder(X))
