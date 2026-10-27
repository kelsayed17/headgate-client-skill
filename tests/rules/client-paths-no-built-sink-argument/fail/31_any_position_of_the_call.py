import os

class C:
    @retry
    async def m(self, s: str) -> None:
        x = 1
        await self.get(  # the bars
            f"/v2/{s}/bars",
        )
