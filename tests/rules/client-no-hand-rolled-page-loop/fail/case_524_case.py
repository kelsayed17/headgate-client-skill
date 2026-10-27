async def m(self):
    while True:
        await (self.get("/x"))
