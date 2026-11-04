# A decorated public method is read too.
class C(AsyncBaseClient):
    @traced
    async def get_report(self) -> str:
        return await self.get("report", expect=decoder(str))
