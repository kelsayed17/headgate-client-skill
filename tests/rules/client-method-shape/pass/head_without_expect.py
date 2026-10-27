# headgate 0.6.0: `head()` reads `expect=nothing` when no `expect=` is given.
class C(AsyncBaseClient):
    async def check_available(self) -> None:
        await self.head("status")
