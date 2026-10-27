async def m(self):
    async for _ in range(3):
        await self.get("/x")
