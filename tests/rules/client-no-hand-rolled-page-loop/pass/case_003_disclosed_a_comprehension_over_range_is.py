# DISCLOSED: a comprehension over range() is not a loop statement.
async def pages(self) -> list[Page]:
    return [await self.get(f"/p/{i}") for i in range(5)]
