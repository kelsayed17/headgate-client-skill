# A `type` statement alias of `str`.
type Raw = str


class C(AsyncBaseClient):
    async def get_report(self) -> Raw:
        return await self.get("report", expect=decoder(Raw))
