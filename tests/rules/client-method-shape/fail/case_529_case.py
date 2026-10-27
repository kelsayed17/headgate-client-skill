class C(AsyncBaseClient):
    async def get_x(self) -> X:
        return await self.post("x", expect=as_bytes, retry=RETRY_EVERY_METHOD)
