async def m(self):
    for page in itertools.count():
        await self.get("/x")
