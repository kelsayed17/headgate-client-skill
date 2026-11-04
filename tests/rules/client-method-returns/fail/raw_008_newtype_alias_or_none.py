# A `NewType` over `bytes`, as one arm of `| None`.
from typing import NewType

Raw = NewType("Raw", bytes)


class C(AsyncBaseClient):
    async def get_report(self) -> Raw | None:
        return await self.get("report", expect=Expect(decoder(Raw)).on(404, nothing))
