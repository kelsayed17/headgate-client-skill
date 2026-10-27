# A parenthesised range, an unbounded count() bare and qualified, an async for.
async def m(self):
    for _ in (range(5)):
        await self.get("/x")
