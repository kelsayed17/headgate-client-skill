# The fetch in the loop's condition, its `else`, a def nested in it; parenthesised awaits and callees.
async def m(self):
    while (page := await self.get("/x")).next:
        pass
