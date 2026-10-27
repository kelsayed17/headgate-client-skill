async def m(self):
    for page in count(1):
        await self.get("/x", params={"page": page})
