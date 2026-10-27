# headgate 0.6.0: `head()` with no `expect=` reads `nothing`, so the method is `-> None`.
class C(AsyncBaseClient):
    async def check_available(self) -> None:
        await self.head("status")
