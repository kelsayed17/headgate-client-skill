# `-> str` is a raw return even when a decoder produces it.
class C(AsyncBaseClient):
    async def get_report(self) -> str:
        return await self.get("report", expect=decoder(str))
