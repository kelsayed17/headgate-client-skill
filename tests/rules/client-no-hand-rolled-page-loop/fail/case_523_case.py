async def m(self):
    while True:
        async def one():
            return await self.get("/x")

        await one()
