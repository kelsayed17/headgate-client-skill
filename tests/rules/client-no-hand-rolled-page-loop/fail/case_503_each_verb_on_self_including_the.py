# Each verb on self, including the private plumbing.
async def m(self):
    while True:
        await self.put("/x")
