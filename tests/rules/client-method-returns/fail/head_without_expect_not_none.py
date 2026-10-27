class C(AsyncBaseClient):
    async def check_available(self) -> Status:
        return await self.head("status")
