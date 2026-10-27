class C(AsyncBaseClient):
    async def cancel(self, o: str) -> None:
        await self.delete(t"a/{o}", expect=nothing, timeout=nothing)
