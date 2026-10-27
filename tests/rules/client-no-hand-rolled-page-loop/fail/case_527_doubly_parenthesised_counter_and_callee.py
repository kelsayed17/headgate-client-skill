# Doubly parenthesised counter and callee.
async def m(self):
    for _ in ((range(5))):
        await self.get("/x")
